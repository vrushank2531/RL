from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.tasks import TASKS
from server.environment import CodeDebuggerEnv
from server.models import Action, ResetRequest, Reward

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

from typing import Dict
from fastapi import HTTPException

envs: Dict[str, CodeDebuggerEnv] = {}


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
def reset(request: Optional[ResetRequest] = None):
    task_id = request.task_id if request is not None else 1
    env = CodeDebuggerEnv()
    observation = env.reset(task_id=task_id)
    envs[env.episode_id] = env
    return {"observation": observation, "state": env.state()}


@app.post("/step")
def step(request: Action):
    env = envs.get(request.episode_id)
    if not env:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    observation, reward, done = env.step(request.fixed_code)
    state = env.state()
    
    if done:
        envs.pop(request.episode_id, None)
        
    return {
        "observation": observation,
        "reward":      reward,
        "done":        done,
        "state":       state,
    }


@app.get("/state")
def state(episode_id: str):
    env = envs.get(episode_id)
    if not env:
        raise HTTPException(status_code=404, detail="Episode not found")
    return env.state()


def main():
    """Entry point for [project.scripts] — starts the uvicorn server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
