"""
Reward shaping module — never returns binary 0/1, always a smooth float in [0.0, 1.0].
Provides partial progress signals, speed bonuses, consistency bonuses, explanation
quality scoring, regression penalties, and progress tracking.

Upgraded reward formula:
  0.3*(grader_score) + 0.4*(tests_passed/tests_total) + 0.2*(explanation_quality) + 0.1*(speed_bonus)
"""
from __future__ import annotations

from models import Action, BugEntry, BugType, Reward


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _keyword_score(text: str, keywords: list[str]) -> float:
    """Fraction of *keywords* that appear (case-insensitive) in *text*."""
    if not keywords:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return hits / len(keywords)


def _explanation_quality(explanation: str, entry: BugEntry) -> float:
    """Score explanation quality 0.0-1.0 based on keyword matching."""
    if not explanation.strip():
        return 0.0

    score = 0.0

    # Generic quality signals: length, specificity
    words = explanation.split()
    if len(words) >= 5:
        score += 0.1
    if len(words) >= 15:
        score += 0.1

    # Task-specific keywords
    if entry.bug_type == BugType.SYNTAX:
        keywords = ["syntax", "missing", "typo", "colon", "indent", "parenthesis",
                     "bracket", "quote", "name", "undefined", "argument", "parameter",
                     "error", "type", "attribute", "key"]
        score += 0.4 * _keyword_score(explanation, keywords)

    elif entry.bug_type == BugType.LOGIC:
        keywords = ["off-by-one", "wrong operator", "base case", "comparison",
                     "integer division", "modulo", "wrong index", "boundary",
                     "edge case", "condition", "return", "loop", "increment",
                     "algorithm", "union", "intersection", "range"]
        score += 0.4 * _keyword_score(explanation, keywords)

    elif entry.bug_type == BugType.SECURITY:
        if entry.security_concepts:
            score += 0.5 * _keyword_score(explanation, entry.security_concepts)
        vuln_words = ["injection", "traversal", "eval", "hardcoded", "secret",
                      "vulnerable", "sanitize", "parameterize", "escape",
                      "deserialization", "pickle", "shell", "command", "unsafe"]
        score += 0.3 * _keyword_score(explanation, vuln_words)

    return _clamp(score)


def _speed_bonus(current_step: int) -> float:
    """Bonus for solving quickly: +0.05 in 1 step, +0.03 in 2 steps."""
    if current_step <= 1:
        return 0.05
    elif current_step <= 2:
        return 0.03
    return 0.0


def _consistency_bonus(action: Action, entry: BugEntry, grader_score: float) -> float:
    """
    +0.05 if agent correctly names bug_type AND achieves grader > 0.5.
    This rewards agents who understand what they're fixing.
    """
    type_match = (
        (action.bug_type == BugType.SYNTAX and entry.bug_type == BugType.SYNTAX) or
        (action.bug_type == BugType.LOGIC and entry.bug_type == BugType.LOGIC) or
        (action.bug_type == BugType.SECURITY and entry.bug_type == BugType.SECURITY)
    )
    if type_match and grader_score > 0.5:
        return 0.05
    return 0.0


def _regression_penalty(previous_test_passed: list[bool] | None, test_passed: list[bool]) -> float:
    """
    -0.15 per test that previously passed but now fails.
    Capped at -0.45.
    """
    if previous_test_passed is None:
        return 0.0
    penalty = 0.0
    for prev, curr in zip(previous_test_passed, test_passed):
        if prev and not curr:
            penalty += 0.15
    return round(min(penalty, 0.45), 4)


# ---------------------------------------------------------------------------
# Per-task reward functions
# ---------------------------------------------------------------------------

def compute_syntax_reward(
    action: Action,
    entry: BugEntry,
    test_passed: list[bool],
    previous_test_passed: list[bool] | None,
    *,
    current_step: int = 1,
) -> Reward:
    """
    Syntax task reward with upgraded formula:
    0.3*(grader_score) + 0.4*(tests_passed/total) + 0.2*(explanation_quality) + 0.1*(speed_bonus)
    """
    components: dict[str, float] = {}

    n_tests = max(len(test_passed), 1)
    tests_ratio = sum(test_passed) / n_tests
    grader = _clamp(tests_ratio)

    # Bug identification bonus
    bug_id_score = 0.0
    explanation = action.bug_explanation.lower()
    if entry.error_message:
        error_keywords = ["syntax", "name", "type", "indent", "attribute", "key", "index", "zero", "missing"]
        for kw in error_keywords:
            if kw in entry.error_message.lower() and kw in explanation:
                bug_id_score += 0.1
                break
    if action.bug_type == BugType.SYNTAX:
        bug_id_score += 0.1
    bug_id_score = min(bug_id_score, 0.2)
    components["bug_identification"] = round(bug_id_score, 4)

    # Explanation quality
    expl_quality = _explanation_quality(action.bug_explanation, entry)
    components["explanation_quality"] = round(expl_quality, 4)

    # Tests component
    components["tests_passed"] = round(tests_ratio, 4)

    # Speed bonus
    speed = _speed_bonus(current_step) if grader >= 0.9 else 0.0
    components["speed_bonus"] = round(speed, 4)

    # Consistency bonus
    consistency = _consistency_bonus(action, entry, grader)
    components["consistency_bonus"] = round(consistency, 4)

    # Regression penalty
    penalty = _regression_penalty(previous_test_passed, test_passed)

    # Progress bonus
    progress = 0.0
    if previous_test_passed is not None:
        prev_count = sum(previous_test_passed)
        curr_count = sum(test_passed)
        if curr_count > prev_count:
            progress = 0.05
    components["progress_bonus"] = progress

    # Final weighted formula
    total = (
        0.3 * grader +
        0.4 * tests_ratio +
        0.2 * expl_quality +
        0.1 * speed +
        bug_id_score +
        consistency +
        progress -
        penalty
    )

    return Reward(
        total=round(_clamp(total), 4),
        components=components,
        progress_bonus=progress,
        penalty=penalty,
        grader_score=round(grader, 4),
    )


def compute_logic_reward(
    action: Action,
    entry: BugEntry,
    test_passed: list[bool],
    previous_test_passed: list[bool] | None,
    *,
    current_step: int = 1,
) -> Reward:
    """
    Logic task reward with upgraded formula:
    0.3*(grader_score) + 0.4*(tests_passed/total) + 0.2*(explanation_quality) + 0.1*(speed_bonus)
    """
    components: dict[str, float] = {}

    n_tests = max(len(test_passed), 1)
    tests_ratio = sum(test_passed) / n_tests

    # Bug identification
    bug_id_score = 0.0
    desc_lower = entry.bug_description.lower()
    expl_lower = action.bug_explanation.lower()
    id_keywords = ["off-by-one", "wrong operator", "base case", "comparison", "integer division",
                    "union", "intersection", "modulo", "wrong index", "wrong base", "wrong return"]
    for kw in id_keywords:
        if kw in desc_lower or kw in expl_lower:
            bug_id_score = 0.1
            break
    if action.bug_type == BugType.LOGIC:
        bug_id_score = max(bug_id_score, 0.05)
    components["bug_identification"] = round(bug_id_score, 4)

    # Explanation quality
    expl_quality = _explanation_quality(action.bug_explanation, entry)
    components["explanation_quality"] = round(expl_quality, 4)

    # Tests component
    components["tests_passed"] = round(tests_ratio, 4)

    grader = _clamp(tests_ratio + (0.1 if bug_id_score > 0 else 0.0))

    # Speed bonus
    speed = _speed_bonus(current_step) if grader >= 0.8 else 0.0
    components["speed_bonus"] = round(speed, 4)

    # Consistency bonus
    consistency = _consistency_bonus(action, entry, grader)
    components["consistency_bonus"] = round(consistency, 4)

    # Regression penalty
    penalty = _regression_penalty(previous_test_passed, test_passed)

    # Progress bonus
    progress = 0.0
    if previous_test_passed is not None:
        if sum(test_passed) > sum(previous_test_passed):
            progress = 0.05
    components["progress_bonus"] = progress

    # Final weighted formula
    total = (
        0.3 * grader +
        0.4 * tests_ratio +
        0.2 * expl_quality +
        0.1 * speed +
        bug_id_score +
        consistency +
        progress -
        penalty
    )

    return Reward(
        total=round(_clamp(total), 4),
        components=components,
        progress_bonus=progress,
        penalty=penalty,
        grader_score=round(grader, 4),
    )


def compute_security_reward(
    action: Action,
    entry: BugEntry,
    vuln_found: bool,
    code_fixed: bool,
    explanation_quality: float,
    previous_best: float,
    *,
    current_step: int = 1,
) -> Reward:
    """
    Security task reward:
      0.4 * vuln_found + 0.4 * code_fixed + 0.2 * explanation_quality
    """
    components: dict[str, float] = {}

    vuln_score = 0.4 if vuln_found else 0.0
    fix_score = 0.4 if code_fixed else 0.0

    # Explanation quality from keyword matching
    expl_score = round(0.2 * explanation_quality, 4)

    components["vulnerability_found"] = vuln_score
    components["code_fixed"] = fix_score
    components["explanation_quality"] = expl_score

    grader = _clamp(vuln_score + fix_score + expl_score)

    # Speed bonus
    speed = _speed_bonus(current_step) if grader >= 0.7 else 0.0
    components["speed_bonus"] = round(speed, 4)

    # Consistency bonus
    consistency = _consistency_bonus(action, entry, grader)
    components["consistency_bonus"] = round(consistency, 4)

    # Progress
    progress = 0.0
    current = vuln_score + fix_score + expl_score
    if current > previous_best and previous_best > 0:
        progress = 0.05
    components["progress_bonus"] = progress

    total = _clamp(current + progress + speed + consistency)

    return Reward(
        total=round(total, 4),
        components=components,
        progress_bonus=progress,
        penalty=0.0,
        grader_score=round(grader, 4),
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def compute_reward(
    action: Action,
    entry: BugEntry,
    *,
    test_passed: list[bool] | None = None,
    previous_test_passed: list[bool] | None = None,
    vuln_found: bool = False,
    code_fixed: bool = False,
    explanation_quality: float = 0.0,
    previous_best: float = 0.0,
    current_step: int = 1,
) -> Reward:
    """Route to the correct per-task reward function based on bug type."""
    if entry.bug_type == BugType.SYNTAX:
        return compute_syntax_reward(
            action, entry, test_passed or [], previous_test_passed,
            current_step=current_step,
        )
    elif entry.bug_type == BugType.LOGIC:
        return compute_logic_reward(
            action, entry, test_passed or [], previous_test_passed,
            current_step=current_step,
        )
    elif entry.bug_type == BugType.SECURITY:
        return compute_security_reward(
            action, entry, vuln_found, code_fixed, explanation_quality, previous_best,
            current_step=current_step,
        )
    else:
        # Fallback — treat as logic
        return compute_logic_reward(
            action, entry, test_passed or [], previous_test_passed,
            current_step=current_step,
        )
