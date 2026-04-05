---
title: CodeBugEnv
emoji: 🐛
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

<div align="center">

# 🐛 CodeBugEnv

**A real-world OpenEnv environment for training AI agents to detect and fix Python bugs**

[![OpenEnv Compatible](https://img.shields.io/badge/OpenEnv-Compatible-brightgreen.svg?style=flat-square)](https://github.com/open-env)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker)](https://www.docker.com/)
[![HuggingFace Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-FFD21E.svg?style=flat-square)](https://huggingface.co/spaces)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

</div>

CodeBugEnv is a deterministic, multi-step training arena designed to push AI coding capabilities beyond simple generation. Agents are dropped into realistically flawed Python environments, tasked with identifying the root cause, and evaluated through automated test executions that yield continuous, shaped reward signals mapping exactly to their incremental progress.

---

## ⚡ See It Live

**Live Environment:** [https://huggingface.co/spaces/sharathilangovanb/codebug-env](https://huggingface.co/spaces/sharathilangovanb/codebug-env)

The live space runs the full FastAPI server and hosts the premium environment dashboard. It features:
- **Live metrics bar** (episodes, success rate, best score)
- **Diff view** for raw vs line-level highlight tracking
- **Canvas sparkline** reward trajectory charts
- **Episode history sidebar** capturing the last 20 episodes
- **Hint system** with progressive reveals upon failure
- **Automated Summary** generating A/B/C/D/F grades
- **Keyboard shortcuts** for rapid expert testing

### Python API Example
To interact with the environment programmatically:

```python
import requests
import json

BASE_URL = "https://sharathilangovanb-codebug-env.hf.space"

# 1. Reset Environment (Start Episode)
print("\n[1] Starting Episode...")
obs = requests.post(f"{BASE_URL}/reset", json={"task_id": "syntax_fix"}).json()["observation"]
print(f"Bug Category: {obs['bug_category']} | Hint: {obs['hint']}")

# 2. Submit Action (Step)
print("\n[2] Submitting Fix...")
action = {
    "fixed_code": "def add(a, b):\n    return a + b",
    "bug_explanation": "Missing colon in function definition.",
    "bug_type": "syntax",
    "confidence": 0.95
}
resp = requests.post(f"{BASE_URL}/step", json={"action": action}).json()

print(f"Reward: {resp['reward']['total']:.3f}")
print(f"Tests Passed: {resp['info']['tests_passed']}/{resp['info']['tests_total']}")
```

---

## 🧠 Why This Exists

* **Coding isn't just generation.** Real-world software engineering requires the ability to read, comprehend, and systematically repair broken state. Current LLM benchmarks focus overwhelmingly on greenfield generation (`HumanEval`, `MBPP`).
* **Binary evaluation stalls reinforcement learning.** A simple "Pass/Fail" on an entire script tells an RL algorithm very little. CodeBugEnv evaluates the specific bug type, the test pass ratio, and the explanation quality to generate a gradient signal to learn from.
* **Security requires contextual awareness.** Recognizing an inefficient loop is easy; recognizing a hidden `eval()` vulnerability mapping to user input is significantly harder. CodeBugEnv enforces security-first verification.

CodeBugEnv gives researchers a reproducible, scalable benchmark for exactly this.

---

## 🏗️ Environment Design

### Observation Space
Agents receive fully typed JSON objects representing the current debugging context, including live test results and dynamic hints.

```json
{
  "task_id": "logic_fix",
  "code": "def calculate_discount(price, pct):\n    return price - (price * pct / 10)",
  "error_message": "",
  "test_results": [],
  "hint": "Check the percentage logic",
  "difficulty_score": 0.65,
  "bug_category": "math_logic",
  "estimated_steps": 2,
  "current_step": 0,
  "steps_remaining": 5,
  "previous_actions_summary": [],
  "best_score": 0.0,
  "max_steps": 5
}
```

### Action Space
Agents must not only provide the fix but correctly classify the bug and justify their reasoning to unlock maximum reward points.

```json
{
  "fixed_code": "def calculate_discount(price, pct):\n    return price - (price * pct / 100)",
  "bug_explanation": "The formula divided by 10 instead of 100, resulting in a 10x larger discount.",
  "bug_type": "logic",
  "confidence": 0.98
}
```

### Reward Function
The environment abandons binary evaluations in favor of a weighted, multi-dimensional reward formula. This produces distinct, smooth trajectories for RL training.

```text
Reward = (0.3 * Grader_Score) 
       + (0.4 * (Tests_Passed / Tests_Total)) 
       + (0.2 * Explanation_Quality) 
       + (0.1 * Speed_Bonus)

Modifiers:
+ +0.05 / +0.03 (Speed bonus if solved on step 1 / step 2)
+ +0.05 (Consistency bonus if bug_type accurately classified)
- -0.15 (Regression penalty per test case broken from previous step)
```

### Episode Lifecycle
```ascii
[RESET] ───────────────────────────────────────────────┐
  │                                                    │
  ▼                                                    │
[STEP] ──► (Run Tests) ──► (Compute Reward) ──► Done? ─┴─► [No]
                               │
                               ▼
                             [Yes] ──► [TERMINATE EPISODE]
```

---

## 📋 Tasks

| Task | Difficulty | Description | Target Score | Test Cases |
|------|-----------|-------------|--------------|------------|
| `syntax_fix` | 🟢 Easy | Fix structural constraints (SyntaxError, IndentationError). | ~0.85 | 3 |
| `logic_fix` | 🟡 Medium | Correct logical flaws resulting in incorrect mathematical/state outputs. | ~0.60 | 5 |
| `security_fix` | 🔴 Hard | Identify unsafe eval, SQL injection, hardcoded secrets, path traversal. | ~0.30 | 3 |

**Syntax Fix**  
The easiest task. Agents simply need to respect Python compiler rules. The highest scoring agents use the compiler traces provided dynamically in the observation to resolve the issue in exactly 1 step.

**Logic Fix**  
Significantly harder. The code compiles perfectly but produces incorrect states. Agents must reverse-engineer the expected intent using the failed test case assertions provided back in the environment observation loop. 

**Security Fix**  
Extremely complex. Even `gpt-4o` struggles heavily here (averaging ~0.28). The code works perfectly, tests pass, but there is a hidden backdoor or unsafe operation. Because the explanation-quality sub-reward heavily weighs the agent's ability to precisely describe the attack vector, simply changing `eval()` to `literal_eval()` without understanding *why* loses points.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker (optional)

### 1. Local Installation

```bash
# 1. Clone & enter repository
git clone https://github.com/sharathilangovanb/codebug-env.git
cd codebug-env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the environment server
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### 2. Verify Health (cURL)
```bash
curl http://localhost:7860/health
# {"status": "healthy"}

curl http://localhost:7860/metrics
# {"total_episodes":...}
```

### 3. Docker Deployment
```bash
docker build -t codebug-env .
docker run -p 7860:7860 codebug-env
```

---

## 📡 API Reference

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Serves dashboard UI | No |
| GET | `/health` | Server status | No |
| POST | `/reset` | Initialize new episode | No |
| POST | `/step` | Execute agent action | No |
| GET | `/state` | Retrieve current episode state | No |
| GET | `/tasks` | List of available environments | No |
| POST | `/grader` | Stateless grader execution | No |
| GET | `/baseline`| Retrieve baseline agent metadata | No |
| GET | `/metrics` | Live session statistics | No |
| GET | `/history` | Last 20 completed episodes | No |
| GET | `/validate` | Self-validation health check | No |

<details>
<summary><strong>View /reset Example</strong></summary>

**Request:**
```json
{
  "task_id": "logic_fix",
  "seed": 42
}
```

**Response:**
```json
{
  "observation": {
    "task_id": "logic_fix",
    ...
  }
}
```
</details>

<details>
<summary><strong>View /step Example</strong></summary>

**Request:**
```json
{
  "action": {
    "fixed_code": "def run(): return True",
    "bug_explanation": "Fixed logical return.",
    "bug_type": "logic",
    "confidence": 0.99
  }
}
```

**Response:**
```json
{
  "observation": { ... },
  "reward": {
    "total": 0.85,
    "grader_score": 0.45
  },
  "done": false,
  "info": {
    "tests_passed": 4,
    "tests_total": 5
  }
}
```
</details>

---

## 📊 Baseline Execution

Due to the stochastic nature of language models, CodeBugEnv integrates a built-in simulation pipeline to generate baseline capabilities. 

If executed without an `OPENAI_API_KEY`, the protocol simulates the upper-bound of the deterministic grader using ground-truth corpora.

| Task | Context | Score |
|------|---------|-------|
| `syntax_fix` | gpt-4o-mini (Simulation) | **1.00** |
| `logic_fix` | gpt-4o-mini (Simulation) | **1.00** |
| `security_fix` | gpt-4o-mini (Simulation) | **0.40** |
| **overall** | gpt-4o-mini (Simulation) | **0.80** |

```bash
# Run simulation (zero cost)
python baseline.py

# Run LLM
export OPENAI_API_KEY="sk-..."
python baseline.py
```

---

<div align="center">
  <sub>Built for the Meta x Scaler OpenEnv Hackathon. License MIT.</sub>
</div>
