import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from hex_minesweeper.config import load_project_env


class ProjectEnvTests(unittest.TestCase):
    def test_loads_values_without_overriding_shell_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "# comment\nFROM_FILE=hello\nQUOTED='world value'\nFROM_SHELL=file\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"FROM_SHELL": "shell"}, clear=True):
                load_project_env(env_file)
                self.assertEqual(os.environ["FROM_FILE"], "hello")
                self.assertEqual(os.environ["QUOTED"], "world value")
                self.assertEqual(os.environ["FROM_SHELL"], "shell")

    def test_missing_env_file_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "absent.env"
            load_project_env(missing)


if __name__ == "__main__":
    unittest.main()
