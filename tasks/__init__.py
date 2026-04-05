"""Tasks package — one module per difficulty tier."""
from tasks.task1_syntax import SyntaxFixTask
from tasks.task2_logic import LogicFixTask
from tasks.task3_security import SecurityFixTask

TASK_REGISTRY: dict[str, type] = {
    "syntax_fix": SyntaxFixTask,
    "logic_fix": LogicFixTask,
    "security_fix": SecurityFixTask,
}

__all__ = ["TASK_REGISTRY", "SyntaxFixTask", "LogicFixTask", "SecurityFixTask"]
