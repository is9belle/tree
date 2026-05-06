from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_tree(sample_path: Path, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "tree.py"), str(sample_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        input=stdin,
        check=False,
    )


def final_program_output(stdout: str) -> str:
    lines = [line.strip() for line in stdout.splitlines()]
    marker = "=== Running program ==="

    if marker not in lines:
        return ""

    start = lines.index(marker) + 1
    for line in lines[start:]:
        if line and not line.startswith("=== Final environment ==="):
            return line

    return ""


class TreeInterpreterTests(unittest.TestCase):
    def test_concat_program(self) -> None:
        """Test that a program with string concatenation works."""
        result = run_tree(ROOT / "tests" / "Input.tree", stdin="hello\n")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("Hello, hello", final_program_output(result.stdout))

    def test_sum_numbers_program(self) -> None:
        """Test the comma regression case to ensure commas in filenames work."""
        # This test verifies that commas are properly quoted in generated code
        result = run_tree(ROOT / "tests" / "Comma.tree")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        # Verify the generated text quotes the comma string correctly
        self.assertIn("print(add('hello, ', 'world'))", result.stdout)
        self.assertIn("hello, world", final_program_output(result.stdout))

    def test_commas_are_quoted(self) -> None:
        result = run_tree(ROOT / "tests" / "Comma.tree")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("print(add('hello, ', 'world'))", result.stdout)
        self.assertIn("hello, world", final_program_output(result.stdout))


if __name__ == "__main__":
    unittest.main()