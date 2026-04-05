from pydantic import BaseModel
from typing import List, Optional


class Action(BaseModel):
    fixed_code: str


class ResetRequest(BaseModel):
    task_id: Optional[int] = 1


class Observation(BaseModel):
    current_code:       str
    task_id:            int
    task_description:   str
    attempts_remaining: int
    test_results:       List[str]


class Reward(BaseModel):
    reward: float
    score:  float
    passed: int
    total:  int


class State(BaseModel):
    episode_id: str
    step_count: int
    done:       bool
    reward:     float
    score:      float
