"""
Task 1 — Syntax Fix (Easy)
Agent receives broken Python code with 1-2 syntax/runtime errors.
Must return corrected code. Graded by running pytest test cases.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from models import Action, BugEntry, BugType, Reward, TaskInfo
from corpus.bug_corpus import get_bugs_by_type
from reward import compute_syntax_reward


TASK_ID = "syntax_fix"
_TIMEOUT = 5  # seconds per test execution


class SyntaxFixTask:
    task_id: str = TASK_ID

    @staticmethod
    def info() -> TaskInfo:
        return TaskInfo(
            task_id=TASK_ID,
            name="Syntax Fix",
            difficulty="easy",
            description=(
                "Agent receives broken Python code with 1-2 syntax or runtime errors "
                "(SyntaxError, NameError, TypeError, etc.). Must return corrected code."
            ),
            target_score="~0.85 (GPT-4o-mini)",
            num_test_cases=3,
            max_steps=5,
        )

    @staticmethod
    def get_bugs() -> list[BugEntry]:
        return get_bugs_by_type(BugType.SYNTAX)

    @staticmethod
    def run_tests(code: str, entry: BugEntry) -> list[bool]:
        """Execute each test case in a subprocess. Returns list of pass/fail bools."""
        results: list[bool] = []
        test_cases = entry.test_cases[:3]  # use exactly 3

        for tc in test_cases:
            # Build a standalone script that defines the function then asserts
            func_name = _extract_func_name(code)
            if not func_name:
                results.append(False)
                continue

            test_script = textwrap.dedent(f"""\
                import json, sys
                {code}

                _input = json.loads(sys.argv[1])
                _expected = json.loads(sys.argv[2])
                if isinstance(_input, list):
                    _result = {func_name}(*_input)
                else:
                    _result = {func_name}(_input)
                assert _result == _expected, f"Got {{_result}}, expected {{_expected}}"
                print("PASS")
            """)

            passed = _exec_test_script(test_script, tc.input, tc.expected_output)
            results.append(passed)

        return results

    @staticmethod
    def grade(action: Action, entry: BugEntry, previous_test_passed: list[bool] | None = None) -> tuple[Reward, list[bool]]:
        """Run tests on the agent's fixed code and compute reward."""
        test_passed = SyntaxFixTask.run_tests(action.fixed_code, entry)
        reward = compute_syntax_reward(action, entry, test_passed, previous_test_passed)
        return reward, test_passed

    @staticmethod
    def grade_score(action: Action, entry: BugEntry) -> tuple[float, dict[str, Any]]:
        """Pure grader: returns (score, details). Deterministic."""
        test_passed = SyntaxFixTask.run_tests(action.fixed_code, entry)
        score = sum(test_passed) / max(len(test_passed), 1)
        return round(score, 4), {
            "tests_passed": sum(test_passed),
            "total_tests": len(test_passed),
            "per_test": test_passed,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_func_name(code: str) -> str | None:
    """Extract the first 'def <name>' from the code."""
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("def "):
            paren = stripped.find("(")
            if paren > 4:
                return stripped[4:paren]
    return None


def _exec_test_script(script: str, test_input: Any, expected: Any) -> bool:
    """Write script to a temp file and execute it with a timeout."""
    import json
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script)
            f.flush()
            tmp_path = f.name

        result = subprocess.run(
            [sys.executable, tmp_path, json.dumps(test_input), json.dumps(expected)],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
        return result.returncode == 0 and "PASS" in result.stdout
    except (subprocess.TimeoutExpired, Exception):
        return False
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass
