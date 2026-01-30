import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
from src.tools.code_modification.patch_generator import PatchGenerator
from src.tools.code_modification.modifier import CodeModifier

class TestPatchGenerator(unittest.TestCase):
    def test_generate_diff_simple(self):
        original = "line1\nline2\nline3\n"
        modified = "line1\nline2 changed\nline3\n"
        file_path = "test.txt"

        diff = PatchGenerator.generate_diff(original, modified, file_path)

        expected_header_a = "--- a/test.txt"
        expected_header_b = "+++ b/test.txt"
        expected_change = "-line2"
        expected_addition = "+line2 changed"

        self.assertIn(expected_header_a, diff)
        self.assertIn(expected_header_b, diff)
        self.assertIn(expected_change, diff)
        self.assertIn(expected_addition, diff)

    def test_generate_multi_file_diff(self):
        modifications = {
            "file1.txt": {
                "original": "foo\n",
                "modified": "bar\n"
            },
            "file2.txt": {
                "original": "hello\n",
                "modified": "world\n"
            }
        }

        diff = PatchGenerator.generate_multi_file_diff(modifications)

        self.assertIn("--- a/file1.txt", diff)
        self.assertIn("+++ b/file1.txt", diff)
        self.assertIn("-foo", diff)
        self.assertIn("+bar", diff)

        self.assertIn("--- a/file2.txt", diff)
        self.assertIn("+++ b/file2.txt", diff)
        self.assertIn("-hello", diff)
        self.assertIn("+world", diff)

class TestCodeModifier(unittest.TestCase):
    def setUp(self):
        # Patch verify_git_availability to avoid actual git check in init
        with patch('src.tools.code_modification.modifier.subprocess.run'):
            self.modifier = CodeModifier()

    @patch('src.tools.code_modification.modifier.subprocess.run')
    def test_apply_patch_success(self, mock_run):
        mock_run.return_value.returncode = 0

        patch_content = "some diff content"
        target_dir = "/tmp/test"

        result = self.modifier.apply_patch(patch_content, target_dir)

        self.assertTrue(result)
        mock_run.assert_called_with(
            ['git', 'apply', '--verbose'],
            input=b'some diff content',
            cwd=str(Path(target_dir).resolve()),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

    @patch('src.tools.code_modification.modifier.subprocess.run')
    def test_apply_patch_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git', stderr=b'error applying patch')

        patch_content = "invalid diff"
        target_dir = "/tmp/test"

        result = self.modifier.apply_patch(patch_content, target_dir)

        self.assertFalse(result)

    @patch('src.tools.code_modification.modifier.subprocess.run')
    def test_revert_patch_success(self, mock_run):
        mock_run.return_value.returncode = 0

        patch_content = "some diff content"
        target_dir = "/tmp/test"

        result = self.modifier.revert_patch(patch_content, target_dir)

        self.assertTrue(result)
        mock_run.assert_called_with(
            ['git', 'apply', '--reverse', '--verbose'],
            input=b'some diff content',
            cwd=str(Path(target_dir).resolve()),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

    @patch('src.tools.code_modification.modifier.subprocess.run')
    def test_check_conflicts_success(self, mock_run):
        mock_run.return_value.returncode = 0

        patch_content = "some diff content"
        target_dir = "/tmp/test"

        result = self.modifier.check_conflicts(patch_content, target_dir)

        self.assertTrue(result)
        mock_run.assert_called_with(
            ['git', 'apply', '--check'],
            input=b'some diff content',
            cwd=str(Path(target_dir).resolve()),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

    @patch('src.tools.code_modification.modifier.subprocess.run')
    def test_check_conflicts_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git', stderr=b'patch does not apply')

        patch_content = "conflicting diff"
        target_dir = "/tmp/test"

        result = self.modifier.check_conflicts(patch_content, target_dir)

        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
