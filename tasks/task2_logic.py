"""
Task 2 — Logic Fix (Medium)
Agent receives code that runs without errors but produces wrong output.
Must diagnose the logical flaw and fix it.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import json
from pathlib import Path
from typing import Any

from models import Action, BugEntry, BugType, Reward, TaskInfo
from corpus.bug_corpus import get_bugs_by_type
from reward import compute_logic_reward


TASK_ID = "logic_fix"
_TIMEOUT = 5


class LogicFixTask:
    task_id: str = TASK_ID

    @staticmethod
    def info() -> TaskInfo:
        return TaskInfo(
            task_id=TASK_ID,
            name="Logic Fix",
            difficulty="medium",
            description=(
                "Agent receives code that runs without errors but produces wrong output. "
                "Must diagnose the logical flaw (off-by-one, wrong operator, wrong algorithm) and fix it."
            ),
            target_score="~0.60 (GPT-4o)",
            num_test_cases=5,
            max_steps=5,
        )

    @staticmethod
    def get_bugs() -> list[BugEntry]:
        return get_bugs_by_type(BugType.LOGIC)

    @staticmethod
    def run_tests(code: str, entry: BugEntry) -> list[bool]:
        """Execute each of the 5 test cases in isolation."""
        results: list[bool] = []
        test_cases = entry.test_cases[:5]
        func_name = _extract_func_name(code)

        for tc in test_cases:
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
                # Handle tuple vs list comparison
                if isinstance(_result, tuple):
                    _result = list(_result)
                assert _result == _expected, f"Got {{_result}}, expected {{_expected}}"
                print("PASS")
            """)
            passed = _exec_test(test_script, tc.input, tc.expected_output)
            results.append(passed)

        return results

    @staticmethod
    def grade(action: Action, entry: BugEntry, previous_test_passed: list[bool] | None = None) -> tuple[Reward, list[bool]]:
        test_passed = LogicFixTask.run_tests(action.fixed_code, entry)
        reward = compute_logic_reward(action, entry, test_passed, previous_test_passed)
        return reward, test_passed

    @staticmethod
    def grade_score(action: Action, entry: BugEntry) -> tuple[float, dict[str, Any]]:
        """Pure grader: score = tests_passed/5 + 0.1 bonus for bug ID."""
        test_passed = LogicFixTask.run_tests(action.fixed_code, entry)
        base = sum(test_passed) / max(len(test_passed), 1)

        # Bug identification bonus
        bonus = 0.0
        desc = entry.bug_description.lower()
        expl = action.bug_explanation.lower()
        id_keywords = ["off-by-one", "wrong operator", "base case", "comparison",
                        "integer division", "modulo", "wrong index", "union", "intersection"]
        for kw in id_keywords:
            if kw in desc or kw in expl:
                bonus = 0.1
                break
        if action.bug_type == BugType.LOGIC:
            bonus = max(bonus, 0.05)

        score = min(base + bonus, 1.0)
        return round(score, 4), {
            "tests_passed": sum(test_passed),
            "total_tests": len(test_passed),
            "per_test": test_passed,
            "bug_id_bonus": bonus,
        }


def _extract_func_name(code: str) -> str | None:
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("def "):
            paren = stripped.find("(")
            if paren > 4:
                return stripped[4:paren]
    return None


def _exec_test(script: str, test_input: Any, expected: Any) -> bool:
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script)
            f.flush()
            tmp_path = f.name
        result = subprocess.run(
            [sys.executable, tmp_path, json.dumps(test_input), json.dumps(expected)],
            capture_output=True, text=True, timeout=_TIMEOUT,
        )
        return result.returncode == 0 and "PASS" in result.stdout
    except (subprocess.TimeoutExpired, Exception):
        return False
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass
