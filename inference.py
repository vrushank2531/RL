"""
inference.py — Code Debugger Environment
=========================================
Runs an LLM agent against all 7 tasks using two models:
  1. The model specified via MODEL_NAME env var (default: Nemotron Super 49B)
  2. A standard OpenAI-compatible model as fallback / comparison

Required environment variables:
    API_BASE_URL   The API endpoint for the LLM  (default: HF Inference Router)
    MODEL_NAME     Primary model identifier       (default: Nemotron Super 49B)
    HF_TOKEN       Your Hugging Face API key      (used as api_key)

Optional:
    OPENAI_API_KEY Alternative API key for OpenAI models
    SERVER_URL     Environment server URL         (default: HF Space URL)

Stdout format (strictly followed — judges parse this):
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...,rn>
"""

import os
import sys
import time
import textwrap
from typing import List, Optional

import requests
from openai import OpenAI

# ── Environment variables ─────────────────────────────────────────────────────
HF_TOKEN          = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME  = os.getenv("LOCAL_IMAGE_NAME")
OPENAI_KEY        = os.getenv("OPENAI_API_KEY", "")

# Primary: Nemotron Super via HF Inference Router (OpenAI-compatible)
HF_BASE_URL      = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
NEMOTRON_MODEL   = os.getenv("MODEL_NAME",   "nvidia/Llama-3.1-Nemotron-Nano-8B-v1")

# Secondary: standard OpenAI
OPENAI_BASE_URL  = "https://api.openai.com/v1"
OPENAI_MODEL     = "gpt-4o-mini"

# OpenEnv sets PING_URL to the env container's base URL.
# Fall back to SERVER_URL or localhost for local testing.
SERVER_URL       = os.getenv("PING_URL") or os.getenv("SERVER_URL", "http://localhost:7860")

BENCHMARK         = "code-debugger-env"
MAX_STEPS         = 5
TEMPERATURE       = 0.2
MAX_TOKENS        = 512
SUCCESS_THRESHOLD = 1.0

# Task id → name mapping (matches openenv.yaml)
TASK_NAME_MAP = {
    1: "syntax-error",
    2: "logic-error",
    3: "bubble-sort-swap",
    4: "fibonacci-base-cases",
    5: "binary-search-bounds",
    6: "lcs-dp-transition",
    7: "bracket-stack",
}

SYSTEM_PROMPT = textwrap.dedent("""
    You are a Python debugging expert. You will be shown broken Python code and
    told what the bug is. Your job is to return ONLY the corrected function —
    no explanation, no markdown, no backticks, just the raw Python code.

    Rules:
    - Return the complete corrected function definition.
    - Do not add imports or extra code outside the function.
    - Do not wrap code in ```python``` or any other formatting.
    - If test results are provided, use them to guide your next fix.
""").strip()


# ── Stdout log helpers (format is strict — do not change) ────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    action_oneline = action.replace("\n", "\\n").replace("\r", "")
    print(
        f"[STEP]  step={step} action={action_oneline} "
        f"reward={reward:.2f} done={str(done).lower()} error={error if error else 'null'}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={','.join(f'{r:.2f}' for r in rewards)}",
        flush=True,
    )


# ── Environment HTTP helpers ──────────────────────────────────────────────────

def wait_for_server(url: str, retries: int = 10, delay: float = 3.0) -> bool:
    """Wait until the env server is reachable. Returns True on success."""
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(f"{url}/", timeout=10)
            if r.status_code < 500:
                print(f"[DEBUG] Server reachable on attempt {attempt}", flush=True)
                return True
        except requests.ConnectionError:
            pass
        print(f"[DEBUG] Waiting for server (attempt {attempt}/{retries})...", flush=True)
        time.sleep(delay)
    return False


def env_get_tasks() -> List[dict]:
    r = requests.get(f"{SERVER_URL}/", timeout=30)
    r.raise_for_status()
    raw = r.json().get("tasks", {})
    return [
        {"id": int(k), "name": TASK_NAME_MAP.get(int(k), f"task-{k}")}
        for k in sorted(raw.keys(), key=int)
    ]


def env_reset(task_id: int) -> tuple:
    r = requests.post(f"{SERVER_URL}/reset", json={"task_id": task_id}, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data["observation"], data["state"]["episode_id"]


def env_step(episode_id: str, fixed_code: str) -> tuple:
    r = requests.post(f"{SERVER_URL}/step", json={"episode_id": episode_id, "fixed_code": fixed_code}, timeout=30)
    r.raise_for_status()
    data = r.json()
    reward_val = data["reward"]["reward"] if isinstance(data["reward"], dict) else data["reward"]
    return data["observation"], float(reward_val), bool(data["done"])


# ── LLM call (same client interface for both models) ─────────────────────────

def get_fix(client: OpenAI, model_name: str, obs: dict) -> str:
    """Ask the LLM to fix the broken code. Returns raw Python code string."""
    test_block = "\n".join(obs.get("test_results", [])) or "No results yet."
    user_prompt = textwrap.dedent(f"""
        Task: {obs['task_description']}

        Broken code:
        {obs['current_code']}

        Test results from last attempt:
        {test_block}

        Return the corrected function only.
    """).strip()

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        # Strip accidental markdown fences
        if text.startswith("```"):
            text = "\n".join(
                line for line in text.splitlines()
                if not line.strip().startswith("```")
            ).strip()
        return text if text else obs["current_code"]
    except Exception as exc:
        print(f"[DEBUG] LLM call failed ({model_name}): {exc}", flush=True)
        return obs["current_code"]


# ── Run one full episode for one task ────────────────────────────────────────

def run_task(client: OpenAI, model_name: str, task: dict) -> dict:
    task_id   = task["id"]
    task_name = task["name"]

    log_start(task=task_name, env=BENCHMARK, model=model_name)

    rewards     = []
    steps_taken = 0
    success     = False

    try:
        obs, episode_id = env_reset(task_id)

        for step in range(1, MAX_STEPS + 1):
            steps_taken = step
            error_msg   = None

            try:
                fixed_code        = get_fix(client, model_name, obs)
                obs, reward, done = env_step(episode_id, fixed_code)
            except Exception as exc:
                error_msg  = str(exc)
                done       = True
                reward     = 0.0
                fixed_code = ""

            rewards.append(reward)
            log_step(step=step, action=fixed_code, reward=reward,
                     done=done, error=error_msg)

            if done:
                success = reward >= SUCCESS_THRESHOLD
                break

    except Exception as exc:
        print(f"[DEBUG] Episode setup error: {exc}", flush=True)

    score = sum(rewards) / len(rewards) if rewards else 0.0
    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {"rewards": rewards, "steps": steps_taken, "success": success, "score": score}


# ── Run all tasks for one model ───────────────────────────────────────────────

def run_model(client: OpenAI, model_name: str, tasks: List[dict]) -> List[float]:
    """Runs all tasks for a given model. Returns list of per-task scores."""
    print(f"\n{'='*60}", flush=True)
    print(f"[MODEL] {model_name}", flush=True)
    print(f"{'='*60}\n", flush=True)

    scores = []
    for task in tasks:
        result = run_task(client, model_name, task)
        scores.append(result["score"])
        print(flush=True)

    avg = sum(scores) / len(scores) if scores else 0.0
    print(f"[SUMMARY] model={model_name} tasks={len(tasks)} avg_score={avg:.3f}", flush=True)
    return scores


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"[DEBUG] Server:          {SERVER_URL}", flush=True)
    print(f"[DEBUG] Primary model:   {NEMOTRON_MODEL}", flush=True)
    print(f"[DEBUG] Secondary model: {OPENAI_MODEL}", flush=True)

    # Wait for the env container to become reachable
    if not wait_for_server(SERVER_URL):
        print("[ERROR] Environment server never became reachable. Exiting.", flush=True)
        sys.exit(1)

    try:
        tasks = env_get_tasks()
    except Exception as exc:
        print(f"[ERROR] Failed to fetch tasks: {exc}", flush=True)
        # Fallback: use the static task map so we can still attempt runs
        tasks = [{"id": tid, "name": tname} for tid, tname in TASK_NAME_MAP.items()]
        print(f"[DEBUG] Using fallback task list: {len(tasks)} tasks", flush=True)

    if not tasks:
        print("[ERROR] No tasks available. Exiting.", flush=True)
        sys.exit(1)

    # ── Model 1: Nemotron Super via HF Inference Router ──────────────────────
    # Uses OpenAI-compatible client pointed at HF's router — same interface.
    # HF_TOKEN is used as the api_key.
    if HF_TOKEN:
        nemotron_client = OpenAI(base_url=HF_BASE_URL, api_key=HF_TOKEN)
        nemotron_scores = run_model(nemotron_client, NEMOTRON_MODEL, tasks)
    else:
        print("[DEBUG] HF_TOKEN not set — skipping Nemotron run", flush=True)
        nemotron_scores = []

    # ── Model 2: OpenAI (gpt-4o-mini) ────────────────────────────────────────
    # Falls back to Nemotron via HF router if no OPENAI_API_KEY is set.
    if OPENAI_KEY:
        openai_client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_KEY)
        openai_scores = run_model(openai_client, OPENAI_MODEL, tasks)
    else:
        print("[DEBUG] OPENAI_API_KEY not set — running second pass with Nemotron", flush=True)
        if HF_TOKEN:
            nemotron_client2 = OpenAI(base_url=HF_BASE_URL, api_key=HF_TOKEN)
            openai_scores = run_model(nemotron_client2, NEMOTRON_MODEL, tasks)
        else:
            openai_scores = []

    # ── Final comparison summary ──────────────────────────────────────────────
    print(f"\n{'='*60}", flush=True)
    print("[FINAL SUMMARY]", flush=True)
    if nemotron_scores:
        print(f"  Nemotron avg_score : {sum(nemotron_scores)/len(nemotron_scores):.3f}", flush=True)
    if openai_scores:
        print(f"  OpenAI avg_score   : {sum(openai_scores)/len(openai_scores):.3f}", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    main()
