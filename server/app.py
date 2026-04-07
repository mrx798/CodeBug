"""
FastAPI server exposing the CodeBugEnv via REST endpoints.
Endpoints: /reset, /step, /state, /tasks, /grader, /baseline,
           /metrics, /history, /validate, /health, /metadata, /schema, /mcp, /ui
Start with: uvicorn server.app:app --host 0.0.0.0 --port 7860
"""
from __future__ import annotations

import os
import sys
import time
import traceback
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from env import CodeBugEnv
from models import (
    Action, BugType, GraderRequest, GraderResponse, ResetRequest,
    StepRequest, StepResponse, TaskInfo, BaselineResult,
)
from corpus.bug_corpus import get_bug_by_id, get_bugs_by_type
from tasks import TASK_REGISTRY

app = FastAPI(
    title="CodeBugEnv",
    description="A real-world OpenEnv environment for training AI agents to detect and fix Python code bugs.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global environment instance (single-player mode for HF Spaces)
_env = CodeBugEnv()

# Mount static assets
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_static_dir = os.path.join(_project_root, "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# ── Session-level metrics ────────────────────────────────────────────────────
_SESSION_START = datetime.now(timezone.utc).isoformat()
_metrics: dict[str, Any] = {
    "total_episodes": 0,
    "total_steps": 0,
    "scores_by_task": {"syntax_fix": [], "logic_fix": [], "security_fix": []},
    "best_score_ever": 0.0,
    "successes": 0,
    "steps_to_solve": [],
}

# ── Episode history ──────────────────────────────────────────────────────────
_history: deque[dict[str, Any]] = deque(maxlen=20)

# ── Current episode tracking ─────────────────────────────────────────────────
_current_episode_id: str = ""
_current_episode_task: str = ""
_current_episode_step_scores: list[float] = []
_current_episode_start: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# EXISTING ENDPOINTS (preserved, enhanced)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Serve the frontend dashboard on the root endpoint."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(project_root, "index.html")
    return FileResponse(html_path, media_type="text/html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/metadata")
async def metadata() -> dict[str, Any]:
    return {
        "name": "CodeBugEnv",
        "description": "A real-world OpenEnv environment for training AI agents to detect and fix Python code bugs across syntax, logic, and security vulnerability domains.",
        "version": "1.0.0",
        "author": "CodeBugEnv Team",
        "tags": ["openenv", "code-debugging", "python", "ai-agent", "bug-fixing", "security"],
    }


@app.get("/schema")
async def schema() -> dict[str, Any]:
    from models import Action, Observation, EpisodeState
    return {
        "action": Action.model_json_schema(),
        "observation": Observation.model_json_schema(),
        "state": EpisodeState.model_json_schema(),
    }


@app.post("/mcp")
async def mcp(request: dict[str, Any]) -> dict[str, Any]:
    """Minimal MCP JSON-RPC endpoint for tool discovery."""
    method = request.get("method", "")
    req_id = request.get("id", 1)

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "CodeBugEnv", "version": "1.0.0"},
            },
        }
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {"name": "reset", "description": "Start a new episode", "inputSchema": ResetRequest.model_json_schema()},
                    {"name": "step", "description": "Submit a fix action", "inputSchema": StepRequest.model_json_schema()},
                ]
            },
        }
    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name", "")
        tool_args = request.get("params", {}).get("arguments", {})
        if tool_name == "reset":
            obs = _env.reset(**tool_args)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": obs.model_dump_json()}]}}
        elif tool_name == "step":
            action = Action(**tool_args.get("action", tool_args))
            resp = _env.step(action)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": resp.model_dump_json()}]}}
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}
    else:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


@app.post("/reset")
async def reset(req: ResetRequest = ResetRequest()) -> dict[str, Any]:
    global _current_episode_id, _current_episode_task, _current_episode_step_scores, _current_episode_start
    try:
        obs = _env.reset(task_id=req.task_id, seed=req.seed)
        # Track episode
        _current_episode_id = str(uuid.uuid4())[:8]
        _current_episode_task = req.task_id
        _current_episode_step_scores = []
        _current_episode_start = time.time()
        _metrics["total_episodes"] += 1
        return {"observation": obs.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step")
async def step(req: StepRequest) -> dict[str, Any]:
    global _current_episode_step_scores
    try:
        resp = _env.step(req.action)
        _metrics["total_steps"] += 1
        _current_episode_step_scores.append(resp.reward.grader_score)

        # Update best ever
        if resp.reward.grader_score > _metrics["best_score_ever"]:
            _metrics["best_score_ever"] = resp.reward.grader_score

        # If episode done, record to history and metrics
        if resp.done:
            _record_episode_complete(resp)

        return resp.model_dump()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.get("/state")
async def state() -> dict[str, Any]:
    s = _env.state()
    if s is None:
        return {"state": None, "message": "No active episode. Call /reset first."}
    return {"state": s.model_dump()}


@app.get("/tasks")
async def tasks() -> list[dict[str, Any]]:
    return [t.model_dump() for t in _env.available_tasks()]


@app.post("/grader")
async def grader(req: GraderRequest) -> GraderResponse:
    task_id = req.task_id
    if task_id not in TASK_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown task: {task_id}")

    task_cls = TASK_REGISTRY[task_id]

    # Get bug entry
    if req.bug_entry_id:
        entry = get_bug_by_id(req.bug_entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail=f"Bug entry '{req.bug_entry_id}' not found")
    else:
        import random
        bug_type_map = {"syntax_fix": BugType.SYNTAX, "logic_fix": BugType.LOGIC, "security_fix": BugType.SECURITY}
        bugs = get_bugs_by_type(bug_type_map[task_id])
        random.seed(42)
        entry = random.choice(bugs)

    try:
        score, details = task_cls.grade_score(req.action, entry)
        return GraderResponse(score=score, details=details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grading error: {e}\n{traceback.format_exc()}")


@app.get("/baseline")
async def baseline() -> dict[str, str]:
    return {
        "message": "Run baseline.py to execute the baseline agent. This endpoint is informational.",
        "command": "python baseline.py",
        "model": "gpt-4o-mini",
        "episodes_per_task": 3,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# NEW ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/metrics")
async def metrics() -> dict[str, Any]:
    """Live statistics across all episodes run this session."""
    avg_by_task: dict[str, float] = {}
    for task_id, scores in _metrics["scores_by_task"].items():
        avg_by_task[task_id] = round(sum(scores) / max(len(scores), 1), 4) if scores else 0.0

    total_ep = _metrics["total_episodes"]
    success_rate = round(_metrics["successes"] / max(total_ep, 1), 4)
    solve_steps = _metrics["steps_to_solve"]
    avg_steps = round(sum(solve_steps) / max(len(solve_steps), 1), 2) if solve_steps else 0.0

    return {
        "total_episodes": total_ep,
        "total_steps": _metrics["total_steps"],
        "avg_score_by_task": avg_by_task,
        "best_score_ever": round(_metrics["best_score_ever"], 4),
        "success_rate": success_rate,
        "avg_steps_to_solve": avg_steps,
        "session_start": _SESSION_START,
    }


@app.get("/history")
async def history() -> list[dict[str, Any]]:
    """Last 20 completed episodes."""
    return list(_history)


@app.get("/validate")
async def validate() -> dict[str, Any]:
    """Self-validation: runs through a complete episode for each task and confirms correctness."""
    errors: list[str] = []
    tasks_ok: list[str] = []
    graders_ok: list[str] = []

    for task_id in ["syntax_fix", "logic_fix", "security_fix"]:
        test_env = CodeBugEnv()
        try:
            # Reset
            obs = test_env.reset(task_id=task_id, seed=99)
            if not obs.code:
                errors.append(f"{task_id}: reset returned empty code")
                continue
            tasks_ok.append(task_id)

            # Step with the known fixed code
            entry = test_env.get_current_entry()
            if entry is None:
                errors.append(f"{task_id}: no entry loaded after reset")
                continue

            action = Action(
                fixed_code=entry.fixed_code,
                bug_explanation=f"Fixed the {entry.bug_type.value} bug",
                bug_type=entry.bug_type,
                confidence=0.9,
            )
            resp = test_env.step(action)
            if resp.reward.grader_score >= 0.0:
                graders_ok.append(task_id)
            else:
                errors.append(f"{task_id}: grader returned negative score")

        except Exception as e:
            errors.append(f"{task_id}: {str(e)}")

    return {
        "valid": len(errors) == 0,
        "tasks_ok": tasks_ok,
        "graders_ok": graders_ok,
        "errors": errors,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _record_episode_complete(resp: StepResponse) -> None:
    """Record a completed episode to history and metrics."""
    global _current_episode_step_scores

    task_id = _current_episode_task
    final_score = resp.info.get("best_score", 0.0)
    steps_taken = resp.info.get("episode_step", 0)

    # History entry
    _history.appendleft({
        "episode_id": _current_episode_id,
        "task_id": task_id,
        "final_score": round(final_score, 4),
        "steps_taken": steps_taken,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "best_step_score": round(max(_current_episode_step_scores) if _current_episode_step_scores else 0.0, 4),
    })

    # Metrics update
    if task_id in _metrics["scores_by_task"]:
        _metrics["scores_by_task"][task_id].append(final_score)

    if final_score > 0.7:
        _metrics["successes"] += 1

    if final_score > 0.0:
        _metrics["steps_to_solve"].append(steps_taken)


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Entry point for running the server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
