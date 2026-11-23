import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name(
    "check_non_ascii_module_paths.py"
).resolve()


class GitIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")

        self.write("src/Legacy₂.lean")
        self.write("src/Plain.lean")
        self.commit("initial")

    def git(self, *args):
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        )

    def write(self, name, content="-- fixture\n"):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def check(self):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, str(SCRIPT), "HEAD~1", "HEAD"],
            cwd=self.repo,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_ascii_addition_allowed(self):
        self.write("src/New2.lean")
        self.commit("add ASCII file")
        self.assertEqual(self.check().returncode, 0)

    def test_unicode_addition_rejected(self):
        self.write("src/New₂.lean")
        self.commit("add Unicode file")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("New₂.lean", result.stdout)

    def test_unicode_rename_rejected(self):
        (self.repo / "src/Plain.lean").rename(
            self.repo / "src/Plain₂.lean"
        )
        self.commit("rename to Unicode")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Plain₂.lean", result.stdout)

    def test_existing_unicode_edit_allowed(self):
        self.write("src/Legacy₂.lean", "-- modified\n")
        self.commit("edit legacy file")
        self.assertEqual(self.check().returncode, 0)

    def test_unicode_deletion_allowed(self):
        (self.repo / "src/Legacy₂.lean").unlink()
        self.commit("delete legacy file")
        self.assertEqual(self.check().returncode, 0)


if __name__ == "__main__":
    unittest.main()
