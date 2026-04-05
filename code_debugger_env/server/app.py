from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tasks import TASKS
from environment import CodeDebuggerEnv
from models import Action, ResetRequest

app = FastAPI(
    title="Code Debugger Environment",
    description="An RL environment where an AI agent fixes broken Python code",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = CodeDebuggerEnv()


@app.get("/")
def root():
    return {
        "name": "Code Debugger Environment",
        "description": f"Fix broken Python code across {len(TASKS)} tasks",
        "tasks": {
            k: f"{v['difficulty'].capitalize()} — {v['description']}"
            for k, v in TASKS.items()
        },
        "endpoints": {
            "POST /reset": "Start a new episode — body: {task_id: 1}",
            "POST /step":  "Submit a fix    — body: {fixed_code: '...'}",
            "GET  /state": "Episode metadata",
        },
    }


@app.post("/reset")
def reset(request: ResetRequest):
    observation = env.reset(task_id=request.task_id)
    return {"observation": observation, "state": env.state()}


@app.post("/step")
def step(request: Action):
    observation, reward, done = env.step(request.fixed_code)
    return {
        "observation": observation,
        "reward":      reward,
        "done":        done,
        "state":       env.state(),
    }


@app.get("/state")
def state():
    return env.state()
