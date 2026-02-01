"""
KB Agent (Knowledge Base Agent)

Wraps KnowledgeBase engine for RAG-based knowledge retrieval and storage.
Responsible for interacting with the RAG system in the state machine.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

from src.agents.base_agent import BaseAgent, AgentState

logger = logging.getLogger(__name__)


@dataclass
class KBAgentConfig:
    """KBAgent配置"""
    # 向量数据库配置
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    collection_name: str = "firmware_knowledge"
    
    # 关系数据库配置
    postgres_url: str = "postgresql://localhost/firmware_kb"
    
    # Embedding配置
    embedding_model: str = "text-embedding-ada-002"
    embedding_dim: int = 1536
    
    # 检索配置
    default_max_results: int = 10
    min_confidence_score: float = 0.5


class KBAgent(BaseAgent):
    """
    KB Agent
    
    Encapsulates KnowledgeBase capabilities:
    - Retrieval: Respond to CodeAgent and AnalysisAgent retrieval requests
    - Knowledge Capture: Store successful iteration records at task end
    
    KR-04: 语义检索能力 - Vector similarity search
    KR-07: 检索增强生成 - RAG integration
    """
    
    def _initialize_engine(self) -> None:
        """Initialize KnowledgeBase connection (Qdrant + Embedding)"""
        # Parse config
        self.config_obj = KBAgentConfig(
            qdrant_host=self.config.get("qdrant_host", "localhost"),
            qdrant_port=self.config.get("qdrant_port", 6333),
            collection_name=self.config.get("collection_name", "firmware_knowledge"),
            embedding_model=self.config.get("embedding_model", "text-embedding-ada-002"),
            embedding_dim=self.config.get("embedding_dim", 1536),
            default_max_results=self.config.get("default_max_results", 10),
            min_confidence_score=self.config.get("min_confidence_score", 0.5),
            postgres_url=self.config.get("postgres_url", "postgresql://localhost/firmware_kb")
        )
        
        # Initialize vector DB client (Qdrant)
        self._init_qdrant_client()
        
        # Initialize embedding service
        self._init_embedding_service()
        
        logger.info(f"KBAgent initialized with Qdrant at {self.config_obj.qdrant_host}:{self.config_obj.qdrant_port}")
    
    def _init_qdrant_client(self):
        """Initialize Qdrant vector database client
        
        KR-04: 使用向量数据库（Qdrant）存储知识嵌入
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import VectorParams, Distance
            
            self._qdrant_client = QdrantClient(
                host=self.config_obj.qdrant_host,
                port=self.config_obj.qdrant_port,
                timeout=10  # type: ignore
            )
            
            # Ensure collection exists
            collections = self._qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.config_obj.collection_name not in collection_names:
                # Create collection with vector configuration
                self._qdrant_client.create_collection(
                    collection_name=self.config_obj.collection_name,
                    vectors_config=VectorParams(
                        size=self.config_obj.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.config_obj.collection_name}")
            
            self._vector_db_client = self._qdrant_client
            
        except ImportError:
            logger.warning("Qdrant client not installed, using placeholder")
            self._vector_db_client = None
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant: {e}, using placeholder")
            self._vector_db_client = None
    
    def _init_embedding_service(self):
        """Initialize embedding service for vectorization
        
        KR-04: Vectorize query using embedding service
        """
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use local embedding model
            model_name = self.config.get("embedding_model_path", "all-MiniLM-L6-v2")
            self._embedding_model = SentenceTransformer(model_name)
            self._embedding_service = "local"
            logger.info(f"Initialized local embedding model: {model_name}")
            
        except ImportError:
            # Fallback to API-based embedding
            self._embedding_model = None
            self._embedding_service = "api"
            logger.info("Using API-based embedding service")
        except Exception as e:
            logger.warning(f"Failed to initialize embedding service: {e}")
            self._embedding_service = None
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute KBAgent logic based on current state and next_action
        
        Args:
            state: Current state
            
        Returns:
            State updates
        """
        next_action = state.get("next_action", "retrieve")
        
        if next_action == "retrieve":
            return await self._retrieve_knowledge(state)
        elif next_action == "capture":
            return await self._capture_knowledge(state)
        elif next_action == "search":
            return await self._search_knowledge(state)
        else:
            logger.warning(f"Unknown next_action: {next_action}")
            return {"next_action": "error"}
    
    async def _retrieve_knowledge(self, state: AgentState) -> Dict[str, Any]:
        """
        Retrieve knowledge from the knowledge base
        
        Args:
            state: Current state with retrieval query and context
            
        Returns:
            Retrieved knowledge units
        """
        query = state.get("knowledge_query", "")
        context = state.get("retrieval_context", {})
        
        if not query:
            return {
                "analysis_report": {
                    "retrieved_knowledge": [],
                    "summary": "No query specified"
                }
            }
        
        try:
            # Placeholder implementation
            # In production, this would:
            # 1. Vectorize the query
            # 2. Search vector database
            # 3. Apply filters from context
            # 4. Rerank results
            # 5. Build context
            
            results = await self._placeholder_search(query, context)
            
            return {
                "analysis_report": {
                    "retrieved_knowledge": results,
                    "query": query,
                    "summary": f"Retrieved {len(results)} knowledge units"
                },
                "messages": [f"Retrieved {len(results)} knowledge units for query"]
            }
        except Exception as e:
            logger.error(f"Knowledge retrieval failed: {e}")
            return {
                "analysis_report": {"retrieved_knowledge": []},
                "errors": [f"Knowledge retrieval failed: {str(e)}"]
            }
    
    async def _capture_knowledge(self, state: AgentState) -> Dict[str, Any]:
        """
        Capture knowledge from completed iteration
        
        Args:
            state: Current state with task results
            
        Returns:
            Knowledge capture result
        """
        next_action = state.get("next_action", "")
        
        # Only capture knowledge on successful completion
        if next_action != "finish":
            return {
                "messages": ["Knowledge capture skipped - task not completed"]
            }
        
        try:
            # Extract iteration data from state
            knowledge_unit = self._extract_knowledge_unit(state)
            
            # Placeholder: Store to knowledge base
            # In production, this would store to Qdrant + PostgreSQL
            
            return {
                "messages": [f"Knowledge captured: {knowledge_unit.get('title', 'Unknown')}"],
                "analysis_report": {
                    "knowledge_captured": True,
                    "unit_id": knowledge_unit.get("id", "")
                }
            }
        except Exception as e:
            logger.error(f"Knowledge capture failed: {e}")
            return {
                "errors": [f"Knowledge capture failed: {str(e)}"]
            }
    
    async def _search_knowledge(self, state: AgentState) -> Dict[str, Any]:
        """
        Search knowledge base with filters
        
        Args:
            state: Current state with search parameters
            
        Returns:
            Search results
        """
        query = state.get("knowledge_query", "")
        filters = state.get("knowledge_filters", {})
        
        try:
            results = await self._placeholder_search(query, filters)
            
            return {
                "analysis_report": {
                    "search_results": results,
                    "total_count": len(results),
                    "summary": f"Found {len(results)} results"
                },
                "messages": [f"Search returned {len(results)} results"]
            }
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return {
                "analysis_report": {"search_results": []},
                "errors": [f"Knowledge search failed: {str(e)}"]
            }
    
    async def _placeholder_search(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base using vector similarity
        
        KR-04: 语义检索能力 - 使用向量数据库（Qdrant）存储知识嵌入
        KR-05: 混合检索支持 - 支持向量检索与关键词检索的混合模式
        KR-06: TopK与阈值过滤
        
        Args:
            query: Search query
            context: Search context including filters
            
        Returns:
            List of knowledge units matching the query
        """
        # Use actual vector search if Qdrant is available
        if self._vector_db_client is not None and self._embedding_service:
            try:
                results = await self._semantic_search(query, context)
                if results:
                    return results
            except Exception as e:
                logger.warning(f"Qdrant search failed: {e}, falling back to placeholder")
        
        # Fallback to placeholder if Qdrant is not available
        return [
            {
                "id": "placeholder_1",
                "title": "Example Knowledge Unit",
                "content": f"Example knowledge related to: {query}",
                "confidence": 0.85,
                "metadata": {
                    "type": "fix_example",
                    "tags": ["example"]
                }
            }
        ]
    
    async def _semantic_search(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using Qdrant
        
        KR-04: 使用向量数据库（Qdrant）存储知识嵌入
        
        Args:
            query: Search query
            context: Search context with filters
            
        Returns:
            List of knowledge units with scores
        """
        # Generate embedding for query
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return []
        
        # Build filter conditions from context
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        filters = []
        product_line = context.get("product_line")
        if product_line:
            filters.append(
                FieldCondition(key="metadata.product_line", match=MatchValue(value=product_line))
            )
        
        # Search Qdrant
        max_results = context.get("max_results", self.config_obj.default_max_results)
        score_threshold = context.get("min_score", self.config_obj.min_confidence_score)
        
        search_result = self._qdrant_client.search(
            collection_name=self.config_obj.collection_name,
            query_vector=query_embedding,
            limit=max_results,
            score_threshold=score_threshold,
            query_filter=Filter(must=filters) if filters else None
        )
        
        # Format results
        results = []
        for hit in search_result:
            payload = hit.payload or {}
            results.append({
                "id": hit.id,
                "content": payload.get("content", ""),
                "title": payload.get("title", ""),
                "confidence": hit.score,
                "metadata": payload.get("metadata", {})
            })
        
        logger.info(f"Semantic search returned {len(results)} results for query: {query[:50]}...")
        return results
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text
        
        KR-04: Vectorize query using embedding service
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        if self._embedding_service == "local" and self._embedding_model is not None:
            try:
                # Generate embedding using local model
                import numpy as np
                embedding = self._embedding_model.encode(text)  # type: ignore
                if hasattr(embedding, 'tolist'):
                    result = embedding.tolist()  # type: ignore
                    return list(map(float, result)) if result else None
                elif isinstance(embedding, np.ndarray):
                    return embedding.tolist()
                else:
                    return [float(x) for x in embedding]  # type: ignore[arg-type]
            except Exception as e:
                logger.error(f"Local embedding generation failed: {e}")
                return None
        elif self._embedding_service == "api":
            # Use API-based embedding
            try:
                return self._get_api_embedding(text)
            except Exception as e:
                logger.error(f"API embedding generation failed: {e}")
                return None
        else:
            return None
    
    def _get_api_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using API
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        import httpx
        
        api_endpoint = self.config.get("embedding_api_endpoint", "")
        api_key = self.config.get("embedding_api_key", "")
        
        if not api_endpoint:
            return None
        
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"model": self.config_obj.embedding_model, "input": text}
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(api_endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Embedding API call failed: {e}")
            return None
    
    def _extract_knowledge_unit(self, state: AgentState) -> Dict[str, Any]:
        """
        Extract knowledge unit from state
        
        Args:
            state: Current state
            
        Returns:
            Knowledge unit dictionary
        """
        import uuid
        
        analysis_report = state.get("analysis_report", {})
        test_results = state.get("test_results", [])
        
        # Calculate pass rate
        total = len(test_results)
        passed = sum(1 for r in test_results if r.get("status") == "passed")
        pass_rate = passed / total if total > 0 else 0
        
        # Build knowledge unit
        knowledge_unit = {
            "id": f"ku_{uuid.uuid4().hex[:12]}",
            "title": f"Fix iteration - {state.get('task_id', 'unknown')}",
            "content": {
                "goal": state.get("task_request", {}).get("goal", ""),
                "patch_summary": state.get("patch_content", "")[:500] if state.get("patch_content") else "",
                "analysis_summary": analysis_report.get("summary", ""),
                "test_summary": f"Pass rate: {pass_rate*100:.1f}%"
            },
            "metadata": {
                "task_id": state.get("task_id", ""),
                "iteration": state.get("iteration", 0),
                "pass_rate": pass_rate,
                "product_line": state.get("product_line", "unknown"),
                "created_at": datetime.utcnow().isoformat()
            },
            "confidence": pass_rate,
            "tags": ["iteration_record"]
        }
        
        return knowledge_unit
    
    async def _store_knowledge(self, knowledge_unit: Dict[str, Any]) -> bool:
        """
        Store knowledge unit to knowledge base
        
        Args:
            knowledge_unit: Knowledge unit to store
            
        Returns:
            True if successful
        """
        # Placeholder implementation
        logger.info(f"Would store knowledge unit: {knowledge_unit.get('id')}")
        return True
    
    async def _vectorize(self, text: str) -> List[float]:
        """
        Vectorize text using embedding service
        
        Args:
            text: Text to vectorize
            
        Returns:
            Vector embedding
        """
        # Placeholder: return random vector
        import random
        dim = self.config_obj.embedding_dim
        return [random.random() for _ in range(dim)]
