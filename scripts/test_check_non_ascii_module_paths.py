import importlib.util
import pathlib
import unittest
from unittest.mock import patch

script = pathlib.Path(__file__).with_name(
    "check_non_ascii_module_paths.py"
)
spec = importlib.util.spec_from_file_location("path_guard", script)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class PathGuardTests(unittest.TestCase):

    def test_ascii_names_allowed(self):
        paths = [
            "src/Foo.lean",
            "src/Bar2.lean",
        ]
        self.assertEqual(guard.find_violations(paths), [])

    def test_unicode_path_rejected(self):
        paths = ["src/Foo₂.lean"]
        self.assertEqual(guard.find_violations(paths), paths)

    def test_unicode_directory_rejected(self):
        paths = ["src/Folder₂/Foo.lean"]
        self.assertEqual(guard.find_violations(paths), paths)

    def test_non_lean_files_ignored(self):
        paths = ["src/설명.txt"]
        self.assertEqual(guard.find_violations(paths), [])

    @patch.object(guard.subprocess, "run")
    def test_git_changed_paths(self, mock_run):
        mock_run.return_value.stdout = (
            "src/New.lean\0src/Old₂.lean\0".encode("utf-8")
        )

        paths = guard.changed_paths("base", "head")

        self.assertEqual(
            paths,
            ["src/New.lean", "src/Old₂.lean"]
        )
        self.assertIn(
            "--diff-filter=A",
            mock_run.call_args.args[0]
        )


if __name__ == "__main__":
    unittest.main()
