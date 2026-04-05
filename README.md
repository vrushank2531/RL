---
title: Code Debugger Environment
emoji: 🐛
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
---

# Code Debugger Environment

## Description & Motivation

Code Debugger Env is an **RL training environment** where an agent is given broken Python code and must submit a corrected version. Rewards are based on how many test cases pass.

The motivation is to train AI agents that can perform **program repair** — a practically useful skill that requires understanding code semantics, not just syntax. Unlike text generation tasks, this environment gives the agent a grounded, executable signal: the code either works or it doesn't. This makes it well suited for reinforcement learning from code execution feedback (RLCEF).

The environment follows the standard `reset → step → done` loop, exposed over HTTP so any language or framework can interact with it.

---

## Action Space

The agent submits one action per step: a complete Python function as a string.

```json
POST /step
{
  "episode_id": "f0fc0da7-...",
  "fixed_code": "def add_numbers(a, b):\n    return a + b"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `fixed_code` | `string` | Complete Python function. Must define the expected function name. |

The agent has **5 attempts** per episode. Each attempt consumes one step regardless of outcome.

---

## Observation Space

After every `reset` and `step` the server returns:

```json
{
  "current_code":       "def add_numbers(a, b)\n    return a + b",
  "task_id":            1,
  "task_description":   "Fix the syntax error — this function is missing a colon",
  "attempts_remaining": 5,
  "test_results":       ["test 1: PASS — got 5", "test 2: FAIL — expected 0, got 1"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `current_code` | `string` | The broken code on first observation; agent's last submission after that |
| `task_id` | `int` | Which task is active (1–7) |
| `task_description` | `string` | Natural language description of the bug |
| `attempts_remaining` | `int` | Steps left before episode ends (starts at 5) |
| `test_results` | `list[string]` | One result per test case: PASS / FAIL / ERROR with details |

---

## Tasks

| ID | Difficulty | Function | Bug | What to fix |
|----|------------|----------|-----|-------------|
| 1 | Easy | `add_numbers` | Syntax error | Missing `:` at end of `def` line |
| 2 | Easy | `get_max` | Logic error | `<` should be `>` in the comparison |
| 3 | Medium | `bubble_sort` | Algorithm error | `arr[j] = arr[j+1]` overwrites instead of swapping |
| 4 | Medium | `fibonacci` | Recursion bug | Base cases `return 0` and `return 1` are swapped |
| 5 | Medium | `binary_search` | Off-by-one error | `high` initialised to `len(arr) - 2` instead of `len(arr) - 1` |
| 6 | Hard | `lcs` | DP transition bug | Match branch sets `dp[i][j] = dp[i-1][j-1]` instead of `dp[i-1][j-1] + 1` |
| 7 | Hard | `is_balanced` | Stack logic bug | On bracket match, code pushes to stack instead of popping |

**Difficulty rationale:**
- **Easy** — single token fix, error is visible at a glance
- **Medium** — requires understanding the algorithm's intent
- **Hard** — requires knowing the correct algorithm to spot the subtle logical mistake

---

## Reward Function

| Outcome | Reward | Score |
|---------|--------|-------|
| All test cases pass | **1.0** | 1.0 |
| Some test cases pass | **score** | 0.0 – 1.0 |
| No test cases pass | **0.0** | 0.0 |
| Code crashes / syntax error | **0.0** | 0.0 |

`score = passed / total`. Episode ends when all tests pass or attempts run out.

---

## Baseline Scores

Scores are **deterministic** — same code submitted always produces the same reward (confirmed across repeated runs).

| Task | Difficulty | Baseline reward (broken code unchanged) | Oracle reward (correct fix) |
|------|------------|----------------------------------------|-----------------------------|
| 1 | Easy | 0.000 (0/3 pass — crashes) | 1.000 |
| 2 | Easy | 0.444 (1/3 pass) | 1.000 |
| 3 | Medium | 0.375 (1/4 pass) | 1.000 |
| 4 | Medium | 0.167 (0/4 pass) | 1.000 |
| 5 | Medium | 0.792 (3/4 pass) | 1.000 |
| 6 | Hard | 0.375 (1/4 pass) | 1.000 |
| 7 | Hard | 0.667 (3/5 pass) | 1.000 |

All rewards are normalised to **[0.0, 1.0]** as required by the OpenEnv spec.

**Baseline agent:** submits the broken code unchanged on every attempt. Average reward: **0.403**
**Oracle agent:** submits the correct fix on attempt 1. Average reward: **1.000**

---

## Setup & Usage

### Run locally with Docker

```bash
# Build
docker build -t code-debugger-env .

# Run
docker run -p 7860:7860 code-debugger-env
```

Server is now at `http://localhost:7860`.

### Interact from Python

```bash
pip install requests
```

```python
import sys
sys.path.insert(0, "code_debugger_env")
from client import CodeDebuggerClient

# local
client = CodeDebuggerClient("http://localhost:7860")

# or on HF
client = CodeDebuggerClient("https://vrushank2531-code-debugger-env.hf.space")

obs, episode_id = client.reset(task_id=1)
print(obs["current_code"])        # broken code
print(obs["task_description"])    # what to fix

obs, reward, done = client.step(episode_id, "def add_numbers(a, b):\n    return a + b")
print(reward)   # 1.0
print(done)     # True
```

### API reference

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| GET | `/` | — | Environment info and full task list |
| POST | `/reset` | `{"task_id": 1}` | `{observation, state}` |
| POST | `/step` | `{"episode_id": "...", "fixed_code": "..."}` | `{observation, reward, done, state}` |
| GET | `/state` | `?episode_id=...` | `{episode_id, step_count, done, reward, score}` |

### Project structure

```
hf_v2/
├── Dockerfile                     ← used by Hugging Face Spaces (root required)
├── README.md
└── code_debugger_env/
    ├── client.py                  ← import this in your training script
    ├── models.py                  ← Action, Observation, State definitions
    └── server/
        ├── Dockerfile             ← for local docker build inside server/
        ├── app.py                 ← FastAPI server
        ├── environment.py         ← episode state management
        ├── grader.py              ← test execution and reward logic
        ├── tasks.py               ← all 7 task definitions
        └── requirements.txt
```
