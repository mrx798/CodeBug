"""
CodeBugEnv — Main environment class.
Implements step(action), reset(), state() per OpenEnv spec.
Episode management with max 5 steps, best-score tracking.

Upgraded: enriched /reset observation, enriched /step info, episode timing.
"""
from __future__ import annotations

import random
import time
from typing import Any

from models import (
    Action, BugEntry, BugType, Difficulty, EpisodeState,
    Observation, Reward, StepResponse, TaskInfo,
)
from corpus.bug_corpus import get_bugs_by_type, get_bug_by_id, get_corpus
from tasks.task1_syntax import SyntaxFixTask
from tasks.task2_logic import LogicFixTask
from tasks.task3_security import SecurityFixTask


_TASK_MAP = {
    "syntax_fix": SyntaxFixTask,
    "logic_fix": LogicFixTask,
    "security_fix": SecurityFixTask,
}

_BUG_TYPE_MAP = {
    "syntax_fix": BugType.SYNTAX,
    "logic_fix": BugType.LOGIC,
    "security_fix": BugType.SECURITY,
}

MAX_STEPS = 5

# Maps bug_description keywords to a normalized bug_category label
_BUG_CATEGORY_MAP: dict[str, str] = {
    "missing colon": "missing_colon",
    "unclosed string": "unclosed_string",
    "undefined variable": "undefined_variable",
    "missing argument": "missing_argument",
    "wrong indentation": "wrong_indentation",
    "missing return": "missing_return",
    "missing import": "missing_import",
    "wrong operator": "wrong_operator",
    "off-by-one": "off_by_one",
    "wrong base": "wrong_base_case",
    "wrong comparison": "wrong_comparison",
    "integer division": "integer_division",
    "wrong index": "wrong_index",
    "sql injection": "sql_injection",
    "hardcoded": "hardcoded_secret",
    "eval": "unsafe_eval",
    "path traversal": "path_traversal",
    "deserialization": "insecure_deserialization",
    "command injection": "command_injection",
    "pickle": "insecure_deserialization",
    "yaml": "insecure_deserialization",
}


def _infer_bug_category(entry: BugEntry) -> str:
    """Infer a normalized bug category from the entry's description and metadata."""
    desc = entry.bug_description.lower()
    for keyword, category in _BUG_CATEGORY_MAP.items():
        if keyword in desc:
            return category
    # Fallback: use vulnerability_type if present
    if entry.vulnerability_type:
        return entry.vulnerability_type.value
    # Fallback: generic
    return f"{entry.bug_type.value}_error"


def _estimate_difficulty(entry: BugEntry) -> float:
    """Compute a 0.0–1.0 difficulty score for the specific bug instance."""
    base = {"easy": 0.2, "medium": 0.5, "hard": 0.8}.get(entry.difficulty.value, 0.5)
    # Adjust based on code length and test case count
    code_len = len(entry.buggy_code)
    length_factor = min(code_len / 500.0, 0.2)
    tests_factor = min(len(entry.test_cases) * 0.02, 0.1)
    return round(min(base + length_factor + tests_factor, 1.0), 2)


def _estimate_steps(entry: BugEntry) -> int:
    """Estimate how many steps a good agent typically needs."""
    if entry.difficulty == Difficulty.EASY:
        return 1
    elif entry.difficulty == Difficulty.MEDIUM:
        return 2
    else:
        return 3


def _generate_hint(entry: BugEntry) -> str:
    """Generate a subtle hint about what kind of bug this is (not the fix)."""
    if entry.hints:
        return entry.hints[0]
    if entry.error_message:
        # Extract the error type from the message
        error_type = entry.error_message.split(":")[0].strip() if ":" in entry.error_message else ""
        if error_type:
            return f"This code raises a {error_type}. Look at the error context."
    if entry.vulnerability_type:
        vuln_hints = {
            "sql_injection": "The code constructs database queries in an unsafe way.",
            "hardcoded_secret": "Sensitive values should not appear directly in source code.",
            "unsafe_eval": "User input should never be executed as code.",
            "path_traversal": "File paths should be validated before use.",
            "insecure_deserialization": "Untrusted data should not be deserialized with unsafe loaders.",
            "command_injection": "System commands should not include unvalidated user input.",
        }
        return vuln_hints.get(entry.vulnerability_type.value, "Review the code for security issues.")
    return "Analyze the code carefully for logical or structural issues."


def _progressive_hint(entry: BugEntry, step: int, score: float) -> str:
    """Provide increasingly specific hints if agent is struggling."""
    if score >= 0.3 or step < 2:
        return ""

    # Step 2, low score: general direction hint
    if step == 2:
        return f"Focus on the {entry.bug_type.value} aspect. The bug is in the core logic, not edge cases."

    # Step 3+: more specific hints
    if step >= 3 and entry.hints:
        idx = min(step - 2, len(entry.hints) - 1)
        return entry.hints[idx]

    if step >= 3:
        desc = entry.bug_description
        if desc:
            # Give first 60 chars of description as hint
            return f"Hint: {desc[:60]}..."

    return "Try a fundamentally different approach to your fix."


class CodeBugEnv:
    """OpenEnv-compatible environment for training AI agents to fix Python bugs."""

    def __init__(self) -> None:
        self._state: EpisodeState | None = None
        self._entry: BugEntry | None = None
        self._previous_test_passed: list[bool] | None = None
        self._previous_score: float = 0.0
        self._rng = random.Random(42)
        self._episode_start_time: float = 0.0

    # -----------------------------------------------------------------------
    # OpenEnv interface
    # -----------------------------------------------------------------------

    def reset(self, task_id: str, seed: int | None = None) -> Observation:
        """Start a new episode for the given task. Returns initial observation."""
        if task_id not in _TASK_MAP:
            raise ValueError(f"Unknown task_id '{task_id}'. Choose from {list(_TASK_MAP.keys())}")

        if seed is not None:
            self._rng = random.Random(seed)

        bug_type = _BUG_TYPE_MAP[task_id]
        bugs = get_bugs_by_type(bug_type)
        entry = self._rng.choice(bugs)

        self._entry = entry
        self._previous_test_passed = None
        self._previous_score = 0.0
        self._episode_start_time = time.time()

        obs = Observation(
            task_id=task_id,
            code=entry.buggy_code,
            error_message=entry.error_message,
            test_results=[],
            hints_available=len(entry.hints),
            steps_remaining=MAX_STEPS,
            current_step=0,
            previous_actions_summary=[],
            best_score=0.0,
            max_steps=MAX_STEPS,
            # Enriched fields
            hint=_generate_hint(entry),
            difficulty_score=_estimate_difficulty(entry),
            estimated_steps=_estimate_steps(entry),
            bug_category=_infer_bug_category(entry),
        )

        self._state = EpisodeState(
            task_id=task_id,
            bug_entry_id=entry.id,
            current_step=0,
            max_steps=MAX_STEPS,
            done=False,
            best_score=0.0,
            scores_history=[],
            actions_history=[],
            observation=obs,
        )

        return obs

    def step(self, action: Action) -> StepResponse:
        """Execute one step: grade the agent's fix and return reward + new observation."""
        if self._state is None or self._entry is None:
            raise RuntimeError("Call reset() before step()")
        if self._state.done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        entry = self._entry
        task_id = self._state.task_id
        task_cls = _TASK_MAP[task_id]
        step_num = self._state.current_step + 1

        # Grade based on task type
        tests_passed_count = 0
        tests_total_count = 0

        if task_id == "security_fix":
            reward = task_cls.grade(action, entry, previous_best=self._state.best_score)
            test_results_list: list[dict[str, Any]] = [
                {"test": "vulnerability_id", "passed": reward.components.get("vulnerability_found", 0) > 0},
                {"test": "code_fixed", "passed": reward.components.get("code_fixed", 0) > 0},
                {"test": "explanation", "score": reward.components.get("explanation_quality", 0)},
            ]
            current_test_passed = None
            tests_passed_count = sum(1 for t in test_results_list if t.get("passed", False))
            tests_total_count = 3
        else:
            reward, current_test_passed = task_cls.grade(action, entry, self._previous_test_passed)
            test_results_list = [
                {"test": f"test_{i+1}", "passed": p} for i, p in enumerate(current_test_passed)
            ]
            tests_passed_count = sum(current_test_passed)
            tests_total_count = len(current_test_passed)

        # Calculate improvement delta
        improvement = round(reward.grader_score - self._previous_score, 4)

        # Update state
        self._state.current_step += 1
        self._state.scores_history.append(reward.grader_score)
        self._state.best_score = max(self._state.best_score, reward.grader_score)
        self._state.actions_history.append(action)
        self._previous_score = reward.grader_score

        if current_test_passed is not None:
            self._previous_test_passed = current_test_passed

        # Check done
        done = self._state.current_step >= MAX_STEPS or reward.grader_score >= 1.0
        self._state.done = done

        # Build action summary
        summary = f"Step {self._state.current_step}: score={reward.grader_score:.2f}, type={action.bug_type.value}"
        prev_summaries = [
            f"Step {i+1}: score={s:.2f}"
            for i, s in enumerate(self._state.scores_history[:-1])
        ]
        prev_summaries.append(summary)

        # Progressive hint
        step_hint = _progressive_hint(entry, self._state.current_step, reward.grader_score)

        # Time elapsed
        time_elapsed = round(time.time() - self._episode_start_time, 2)

        obs = Observation(
            task_id=task_id,
            code=entry.buggy_code,
            error_message=entry.error_message,
            test_results=test_results_list,
            hints_available=max(0, len(entry.hints) - self._state.current_step),
            steps_remaining=MAX_STEPS - self._state.current_step,
            current_step=self._state.current_step,
            previous_actions_summary=prev_summaries,
            best_score=self._state.best_score,
            max_steps=MAX_STEPS,
            # Enriched fields
            hint=_generate_hint(entry),
            difficulty_score=_estimate_difficulty(entry),
            estimated_steps=_estimate_steps(entry),
            bug_category=_infer_bug_category(entry),
        )
        self._state.observation = obs

        info: dict[str, Any] = {
            "bug_entry_id": entry.id,
            "best_score": self._state.best_score,
            "episode_step": self._state.current_step,
            # Enriched info fields
            "tests_passed": tests_passed_count,
            "tests_total": tests_total_count,
            "improvement": improvement,
            "hint": step_hint,
            "time_elapsed": time_elapsed,
        }

        return StepResponse(
            observation=obs,
            reward=reward,
            done=done,
            info=info,
        )

    def state(self) -> EpisodeState | None:
        """Return current episode state (for serialisation / checkpointing)."""
        return self._state

    # -----------------------------------------------------------------------
    # Utility
    # -----------------------------------------------------------------------

    @staticmethod
    def available_tasks() -> list[TaskInfo]:
        return [cls.info() for cls in _TASK_MAP.values()]

    def get_current_entry(self) -> BugEntry | None:
        return self._entry
