import uuid
from server.tasks import TASKS
from server.grader import grade, calculate_reward
from server.models import Reward


class CodeDebuggerEnv:
    """
    RL environment — manages episode state.
    Game logic  → tasks.py
    Grading     → grader.py
    API server  → app.py
    """

    def __init__(self):
        self.tasks              = TASKS
        self.current_task_id    = 1
        self.max_attempts       = 5
        self.attempts_remaining = self.max_attempts
        self.step_count         = 0
        self.done               = False
        self.episode_id         = str(uuid.uuid4())
        self.test_results       = []
        self.score              = 0.0
        self.reward             = 0.0
        self.current_code       = TASKS[1]["broken_code"]

    def reset(self, task_id: int = 1):
        """Start a fresh episode for the given task."""
        if task_id not in self.tasks:
            task_id = 1

        self.current_task_id    = task_id
        self.current_code       = self.tasks[task_id]["broken_code"]
        self.attempts_remaining = self.max_attempts
        self.step_count         = 0
        self.done               = False
        self.episode_id         = str(uuid.uuid4())
        self.test_results       = []
        self.score              = 0.0
        self.reward             = 0.0

        return self._observe()

    def step(self, fixed_code: str):
        """AI submits a fix. Returns (observation, reward, done)."""
        if self.done:
            return self._observe(), 0.0, True

        self.step_count         += 1
        self.attempts_remaining -= 1
        self.current_code        = fixed_code

        task = self.tasks[self.current_task_id]
        passed, total, self.test_results, crashed = grade(fixed_code, task)
        self.reward, self.score = calculate_reward(passed, total, crashed)
        
        reward_obj = Reward(reward=self.reward, score=self.score, passed=passed, total=total)

        if passed == total or self.attempts_remaining == 0:
            self.done = True

        return self._observe(), reward_obj, self.done

    def state(self):
        """Return episode metadata."""
        return {
            "episode_id": self.episode_id,
            "step_count": self.step_count,
            "done":       self.done,
            "reward":     self.reward,
            "score":      self.score,
        }

    def _observe(self):
        """Return what the AI currently sees."""
        task = self.tasks[self.current_task_id]
        return {
            "current_code":       self.current_code,
            "task_id":            self.current_task_id,
            "task_description":   task["description"],
            "attempts_remaining": self.attempts_remaining,
            "test_results":       self.test_results,
        }
