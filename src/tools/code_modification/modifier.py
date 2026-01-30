import subprocess
import logging
from pathlib import Path
from typing import Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class CodeModifier:
    """
    Applies and reverts code modifications using patch files.

    This class relies on the 'git' command line tool to apply patches safely,
    supporting conflict detection and reversion.
    """

    def __init__(self, git_path: str = "git"):
        """
        Initialize the CodeModifier.

        Args:
            git_path: Path to the git executable. Defaults to "git".
        """
        self.git_path = git_path
        self._verify_git_availability()

    def _verify_git_availability(self):
        """Verify that git is available in the environment."""
        try:
            subprocess.run(
                [self.git_path, "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning(f"Git executable not found at '{self.git_path}'. Patch operations may fail.")
            # We don't raise an error here to allow instantiation, but methods will fail if git is missing.

    def apply_patch(self, patch_content: str, target_dir: Union[str, Path]) -> bool:
        """
        Apply a patch to the target directory.

        Args:
            patch_content: The content of the unified diff patch.
            target_dir: The directory where the patch should be applied.

        Returns:
            True if the patch was applied successfully, False otherwise.
        """
        target_path = Path(target_dir).resolve()

        if not patch_content.strip():
            logger.warning("Empty patch content provided.")
            return False

        try:
            # git apply reads from stdin
            process = subprocess.run(
                [self.git_path, "apply", "--verbose"],
                input=patch_content.encode('utf-8'),
                cwd=str(target_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            logger.info(f"Patch applied successfully in {target_path}")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"Failed to apply patch: {error_msg}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error applying patch: {str(e)}")
            return False

    def revert_patch(self, patch_content: str, target_dir: Union[str, Path]) -> bool:
        """
        Revert a previously applied patch.

        Args:
            patch_content: The content of the unified diff patch to revert.
            target_dir: The directory where the patch was applied.

        Returns:
            True if the patch was reverted successfully, False otherwise.
        """
        target_path = Path(target_dir).resolve()

        if not patch_content.strip():
            logger.warning("Empty patch content provided.")
            return False

        try:
            # git apply --reverse reads from stdin
            process = subprocess.run(
                [self.git_path, "apply", "--reverse", "--verbose"],
                input=patch_content.encode('utf-8'),
                cwd=str(target_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            logger.info(f"Patch reverted successfully in {target_path}")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"Failed to revert patch: {error_msg}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error reverting patch: {str(e)}")
            return False

    def check_conflicts(self, patch_content: str, target_dir: Union[str, Path]) -> bool:
        """
        Check if the patch can be applied without conflicts (dry-run).

        Args:
            patch_content: The content of the unified diff patch.
            target_dir: The directory where the patch would be applied.

        Returns:
            True if the patch applies cleanly, False if there are conflicts.
        """
        target_path = Path(target_dir).resolve()

        if not patch_content.strip():
            logger.warning("Empty patch content provided.")
            return False

        try:
            # git apply --check reads from stdin and doesn't apply changes
            process = subprocess.run(
                [self.git_path, "apply", "--check"],
                input=patch_content.encode('utf-8'),
                cwd=str(target_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            logger.info(f"Patch check passed for {target_path}")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.info(f"Patch conflict detected: {error_msg}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking patch: {str(e)}")
            return False
