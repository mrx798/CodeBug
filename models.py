"""
CodeBugEnv — Pydantic v2 models for Observation, Action, Reward, and State.

All environment data flows through these typed models to ensure
consistency between the environment, server, and baseline script.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class BugType(str, Enum):
    """Canonical bug categories recognised by the environment."""
    SYNTAX = "syntax"
    LOGIC = "logic"
    SECURITY = "security"
    PERFORMANCE = "performance"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class VulnerabilityType(str, Enum):
    SQL_INJECTION = "sql_injection"
    HARDCODED_SECRET = "hardcoded_secret"
    UNSAFE_EVAL = "unsafe_eval"
    PATH_TRAVERSAL = "path_traversal"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    COMMAND_INJECTION = "command_injection"


# ---------------------------------------------------------------------------
# Test‑case model (used inside the corpus)
# ---------------------------------------------------------------------------

class TestCase(BaseModel):
    """A single pytest‑style test case stored alongside a bug snippet."""
    input: Any = Field(description="Input value(s) for the function under test")
    expected_output: Any = Field(description="Expected return value")
    description: str = Field(default="", description="Human‑readable test label")


# ---------------------------------------------------------------------------
# Corpus entry
# ---------------------------------------------------------------------------

class BugEntry(BaseModel):
    """One record in the synthetic bug corpus."""
    id: str = Field(description="Unique identifier e.g. 'syntax_001'")
    buggy_code: str
    fixed_code: str
    bug_type: BugType
    difficulty: Difficulty
    domain: str = Field(default="general", description="Problem domain e.g. 'sorting', 'api', 'db'")
    bug_description: str = Field(default="")
    vulnerability_type: VulnerabilityType | None = Field(
        default=None,
        description="Only set for security bugs",
    )
    test_cases: list[TestCase] = Field(default_factory=list)
    error_message: str = Field(
        default="",
        description="The traceback or error the buggy code produces (empty for logic/security bugs that run without errors)",
    )
    hints: list[str] = Field(default_factory=list)
    security_concepts: list[str] = Field(
        default_factory=list,
        description="Keywords for explanation‑quality scoring on security tasks",
    )


# ---------------------------------------------------------------------------
# Observation — what the agent sees each step
# ---------------------------------------------------------------------------

class Observation(BaseModel):
    """Rich observation returned by env.state() and env.step()."""
    task_id: str = Field(description="Current task identifier")
    code: str = Field(description="The buggy source code to fix")
    error_message: str = Field(default="", description="Traceback / compiler error (if any)")
    test_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Per-test pass/fail from the *previous* attempt",
    )
    hints_available: int = Field(default=0, description="Number of hints the agent may request")
    steps_remaining: int = Field(description="Steps left in the episode")
    current_step: int = Field(default=0, description="Current step number (0-indexed)")
    previous_actions_summary: list[str] = Field(
        default_factory=list,
        description="Human-readable summaries of prior actions in this episode",
    )
    best_score: float = Field(default=0.0, description="Best grader score achieved so far this episode")
    max_steps: int = Field(default=5, description="Maximum steps per episode")
    # Enriched fields (v2)
    hint: str = Field(default="", description="Subtle hint about the type of bug")
    difficulty_score: float = Field(default=0.5, description="How hard this specific bug instance is (0.0-1.0)")
    estimated_steps: int = Field(default=2, description="How many steps a good agent typically needs")
    bug_category: str = Field(default="", description="Normalized bug category label")


# ---------------------------------------------------------------------------
# Action — what the agent submits
# ---------------------------------------------------------------------------

class Action(BaseModel):
    """Structured action the agent sends to the environment."""
    fixed_code: str = Field(description="The agent's proposed corrected source code")
    bug_explanation: str = Field(default="", description="Free‑text explanation of what the bug was")
    bug_type: BugType = Field(description="Agent's classification of the bug")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Agent's self‑reported confidence")


# ---------------------------------------------------------------------------
# Reward — detailed scoring breakdown
# ---------------------------------------------------------------------------

class Reward(BaseModel):
    """Granular reward returned after each step."""
    total: float = Field(description="Aggregate reward for this step (0.0–1.0 range)")
    components: dict[str, float] = Field(
        default_factory=dict,
        description="Named sub‑scores, e.g. {'tests_passed': 0.33, 'bug_id': 0.1}",
    )
    progress_bonus: float = Field(default=0.0, description="Extra signal for getting closer to solution")
    penalty: float = Field(default=0.0, description="Deductions for regressions or new errors")
    grader_score: float = Field(default=0.0, description="Official grader score for this attempt (0.0–1.0)")


# ---------------------------------------------------------------------------
# State — internal env state exposed via /state
# ---------------------------------------------------------------------------

class EpisodeState(BaseModel):
    """Full internal state of an episode, serialisable for checkpointing."""
    task_id: str
    bug_entry_id: str
    current_step: int = 0
    max_steps: int = 5
    done: bool = False
    best_score: float = 0.0
    scores_history: list[float] = Field(default_factory=list)
    actions_history: list[Action] = Field(default_factory=list)
    observation: Observation | None = None


# ---------------------------------------------------------------------------
# Server request / response helpers
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_id: str = Field(description="Which task to start: 'syntax_fix', 'logic_fix', or 'security_fix'")
    seed: int | None = Field(default=None, description="Optional seed for deterministic bug selection")


class StepRequest(BaseModel):
    action: Action


class StepResponse(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: dict[str, Any] = Field(default_factory=dict)


class TaskInfo(BaseModel):
    task_id: str
    name: str
    difficulty: Difficulty
    description: str
    target_score: str = Field(description="Expected score for reference model e.g. '~0.85'")
    num_test_cases: int
    max_steps: int = 5


class GraderRequest(BaseModel):
    task_id: str
    action: Action
    bug_entry_id: str | None = Field(default=None, description="Specific bug to grade against; random if omitted")


class GraderResponse(BaseModel):
    score: float
    details: dict[str, Any] = Field(default_factory=dict)


class BaselineResult(BaseModel):
    task1: float
    task2: float
    task3: float
    overall: float
