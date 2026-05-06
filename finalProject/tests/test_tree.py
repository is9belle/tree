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
        result = run_tree(ROOT / "Concat.tree", stdin="hello\nworld\nquit\n")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("helloworld", final_program_output(result.stdout))

    def test_sum_numbers_program(self) -> None:
        result = run_tree(ROOT / "SumNums.tree")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("The total of numbers 1-100 is 5050", final_program_output(result.stdout))

    def test_commas_are_quoted(self) -> None:
        result = run_tree(ROOT / "tests" / "Comma.tree")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("print(add('hello, ', 'world'))", result.stdout)
        self.assertIn("hello, world", final_program_output(result.stdout))


if __name__ == "__main__":
    unittest.main()