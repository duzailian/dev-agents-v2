"""
Code Agent

Wraps CodeAnalyzer and CodeModifier engines.
Responsible for code understanding and code modification in the state machine.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.agents.base_agent import BaseAgent, AgentState
from src.tools.code_analysis.analyzer import CodeAnalyzer
from src.tools.code_analysis.parser import TreeSitterParser
from src.tools.code_modification.modifier import CodeModifier
from src.models.code import AnalyzerConfig, AnalysisType

logger = logging.getLogger(__name__)


class CodeAgent(BaseAgent):
    """
    Code Agent
    
    Encapsulates CodeAnalyzer and CodeModifier capabilities:
    - Code Analysis Phase: Analyze code structure and potential issues
    - Patch Generation Phase: Generate patches based on AI suggestions
    - Patch Application Phase: Apply patches and verify syntax
    """
    
    def _initialize_engine(self) -> None:
        """Initialize CodeAnalyzer and CodeModifier engines"""
        # Initialize CodeAnalyzer with config
        analyzer_config = AnalyzerConfig(
            enable_caching=self.config.get("enable_caching", True),
            static_analyzers=self.config.get("static_analyzers", []),
            languages=self.config.get("languages", ["c", "cpp"])
        )
        self.analyzer = CodeAnalyzer(analyzer_config)
        
        # Initialize CodeModifier
        git_path = self.config.get("git_path", "git")
        self.modifier = CodeModifier(git_path=git_path)
        
        logger.info("CodeAgent engines initialized")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute CodeAgent logic based on current state and next_action
        
        Args:
            state: Current state
            
        Returns:
            State updates
        """
        next_action = state.get("next_action", "analyze")
        
        if next_action == "analyze":
            return await self._analyze_code(state)
        elif next_action == "modify":
            return await self._generate_patch(state)
        elif next_action == "apply_patch":
            return await self._apply_patch(state)
        else:
            logger.warning(f"Unknown next_action: {next_action}")
            return {"next_action": "error"}
    
    async def _analyze_code(self, state: AgentState) -> Dict[str, Any]:
        """
        Analyze code in the repository
        
        Args:
            state: Current state containing repo_path and target_files
            
        Returns:
            Analysis results
        """
        repo_path = state.get("repo_path", "")
        target_files = state.get("target_files", [])
        
        if not repo_path:
            return {"errors": ["No repository path specified"]}
        
        # If no specific files, analyze all C/C++ files in repo
        if not target_files:
            target_files = self._find_c_files(repo_path)
        
        if not target_files:
            return {
                "analysis_report": {
                    "files_analyzed": [],
                    "total_issues": 0,
                    "summary": "No C/C++ files found to analyze"
                },
                "messages": ["No files to analyze"]
            }
        
        logger.info(f"Analyzing {len(target_files)} files in {repo_path}")
        
        try:
            # Perform full analysis
            analysis_type = AnalysisType.FULL
            report = await self.analyzer.analyze_files(target_files, analysis_type)
            
            return {
                "analysis_report": {
                    "task_id": report.task_id,
                    "files_analyzed": report.files_analyzed,
                    "total_issues": report.total_issues,
                    "issues_by_severity": report.issues_by_severity,
                    "summary": report.summary,
                    "suggestions": report.suggestions,
                    "dependency_graph": report.dependency_graph,
                    "call_graph": report.call_graph
                },
                "messages": [f"Analyzed {len(target_files)} files, found {report.total_issues} issues"]
            }
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return {
                "errors": [f"Code analysis failed: {str(e)}"],
                "analysis_report": {}
            }
    
    async def _generate_patch(self, state: AgentState) -> Dict[str, Any]:
        """
        Generate patch based on analysis and AI suggestions
        
        Uses LLM to analyze the code issues and generate appropriate fixes.
        Falls back to placeholder if LLM is not configured.
        
        Args:
            state: Current state with analysis_report and task description
            
        Returns:
            Generated patch content
        """
        analysis_report = state.get("analysis_report", {})
        task_description = state.get("task_request", {}).get("goal", "")
        
        # Check if there are issues to fix
        issues = analysis_report.get("total_issues", 0)
        
        if issues == 0:
            return {
                "patch_content": "",
                "messages": ["No issues found, no patch needed"]
            }
        
        # Check if LLM is enabled
        if self.config.get("enable_ai", True):
            try:
                # Generate patch using LLM
                patch_content = await self._generate_patch_with_llm(
                    analysis_report,
                    task_description
                )
                if patch_content:
                    return {
                        "patch_content": patch_content,
                        "next_action": "apply_patch",
                        "messages": [f"Generated patch using LLM for {issues} issues"]
                    }
            except Exception as e:
                logger.warning(f"LLM patch generation failed: {e}, falling back to placeholder")
        
        # Fallback to placeholder if LLM fails or is disabled
        patch_content = self._generate_placeholder_patch(analysis_report)
        
        return {
            "patch_content": patch_content,
            "next_action": "apply_patch",
            "messages": [f"Generated placeholder patch for {issues} issues"]
        }
    
    async def _generate_patch_with_llm(
        self, 
        analysis_report: Dict[str, Any],
        task_description: str
    ) -> str:
        """
        Generate patch content using LLM API
        
        FR-02: C代码自动修改能力（基于AI建议）
        
        Args:
            analysis_report: The code analysis report
            task_description: Description of the task/goal
            
        Returns:
            Git-formatted patch content
        """
        import json
        
        # Build prompt for LLM
        files_analyzed = analysis_report.get("files_analyzed", [])
        issues_by_severity = analysis_report.get("issues_by_severity", {})
        summary = analysis_report.get("summary", "")
        
        prompt = f"""You are a firmware code repair expert. Generate a git patch to fix the identified issues.

Task: {task_description}

Analysis Summary:
{summary}

Files Analyzed: {len(files_analyzed)}
Issues by Severity: {json.dumps(issues_by_severity)}

Please generate a unified diff patch (git format) that fixes the issues.
Only modify the files that have issues. Provide a clear, minimal fix.

Return ONLY the patch content in this format:
```diff
--- a/<filename>
+++ b/<filename>
@@ -line,num +line,num @@
+fixed line
-original line
```

Do not include any other text in your response. If no fix is needed, return "NO_PATCH_NEEDED".
"""
        
        # Call LLM API if configured
        llm_model = self.config.get("llm_model", "gpt-4")
        api_endpoint = self.config.get("api_endpoint", "")
        api_key = self.config.get("api_key", "")
        
        if not api_endpoint or not api_key:
            logger.warning("LLM API not configured, skipping LLM patch generation")
            return ""
        
        try:
            # Note: In production, use the actual LLM API client
            # This is a placeholder for the API call structure
            response = await self._call_llm_api(
                endpoint=api_endpoint,
                api_key=api_key,
                model=llm_model,
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3
            )
            
            # Parse the response to extract patch
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                
                # Extract patch from response
                if "```diff" in content:
                    patch = content.split("```diff")[1].split("```")[0].strip()
                elif "NO_PATCH_NEEDED" in content:
                    return ""
                else:
                    patch = content.strip()
                
                # Validate patch format
                if patch.startswith("--- a/") or patch.startswith("diff --git"):
                    return patch
                else:
                    logger.warning(f"Invalid patch format from LLM: {patch[:100]}")
                    return ""
            
            return ""
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return ""
    
    async def _call_llm_api(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Call LLM API
        
        IR-03: 模型API集成
        
        Args:
            endpoint: API endpoint URL
            api_key: API authentication key
            model: Model name
            prompt: Input prompt
            max_tokens: Maximum tokens in response
            temperature: Temperature for sampling
            
        Returns:
            API response as dictionary
        """
        import httpx
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def _apply_patch(self, state: AgentState) -> Dict[str, Any]:
        """
        Apply the generated patch to the repository
        
        Args:
            state: Current state with patch_content and repo_path
            
        Returns:
            Patch application result
        """
        repo_path = state.get("repo_path", "")
        patch_content = state.get("patch_content", "")
        
        if not patch_content:
            return {
                "errors": ["No patch content to apply"],
                "next_action": "error"
            }
        
        if not repo_path:
            return {
                "errors": ["No repository path specified"],
                "next_action": "error"
            }
        
        # Check for conflicts first
        has_conflicts = not self.modifier.check_conflicts(patch_content, repo_path)
        
        if has_conflicts:
            return {
                "patch_applied": False,
                "errors": ["Patch has conflicts, cannot apply"],
                "next_action": "modify"  # Go back to generate new patch
            }
        
        # Apply the patch
        success = self.modifier.apply_patch(patch_content, repo_path)
        
        if success:
            # Get new commit hash after patch application
            new_commit = self._get_current_commit(repo_path)
            
            return {
                "patch_applied": True,
                "current_commit": new_commit,
                "next_action": "test",  # Proceed to testing
                "messages": ["Patch applied successfully"]
            }
        else:
            return {
                "patch_applied": False,
                "errors": ["Failed to apply patch"],
                "next_action": "modify"
            }
    
    def _find_c_files(self, repo_path: str) -> List[str]:
        """Find all C/C++ files in the repository"""
        c_extensions = ['.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.hxx']
        files = []
        
        repo = Path(repo_path)
        if not repo.exists():
            return files
        
        for path in repo.rglob('*'):
            if path.is_file() and path.suffix.lower() in c_extensions:
                files.append(str(path))
        
        return files
    
    def _generate_placeholder_patch(self, analysis_report: Dict[str, Any]) -> str:
        """
        Generate a placeholder patch (for development/testing)
        
        ⚠️ TODO: This is a placeholder implementation. In production, this should:
        1. Use LLM to analyze the analysis_report
        2. Generate intelligent fixes based on error patterns
        3. Create proper git-formatted patches
        
        Args:
            analysis_report: The code analysis report
            
        Returns:
            Git-formatted patch content (placeholder)
        """
        import uuid
        
        # Generate a simple placeholder patch
        files = analysis_report.get("files_analyzed", [])
        
        if not files:
            return ""
        
        # Simple placeholder: add a comment to the first file
        first_file = files[0]
        patch_content = f"""--- a/{first_file}
+++ b/{first_file}
@@ -1,3 +1,4 @@
 // Auto-generated patch placeholder
 // This patch was generated based on analysis findings
+// TODO: Replace with actual AI-generated fix
 """
        
        return patch_content
    
    def _get_current_commit(self, repo_path: str) -> str:
        """Get the current git commit hash"""
        import subprocess
        
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception:
            return ""
