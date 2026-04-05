import requests


class CodeDebuggerClient:
    """
    Import this in your training code to talk to the running environment.
    Docker container must be running first.

    Usage:
        client = CodeDebuggerClient("http://localhost:7860")
        obs = client.reset(task_id=1)
        obs, reward, done = client.step("def add_numbers(a, b):\\n    return a + b")
        print(client.state())
    """

    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")

    def reset(self, task_id: int = 1):
        """Start a new episode. Returns the first observation."""
        r = requests.post(f"{self.base_url}/reset", json={"task_id": task_id})
        r.raise_for_status()
        return r.json()["observation"]

    def step(self, fixed_code: str):
        """Submit a fix. Returns (observation, reward, done)."""
        r = requests.post(f"{self.base_url}/step", json={"fixed_code": fixed_code})
        r.raise_for_status()
        data = r.json()
        return data["observation"], data["reward"], data["done"]

    def state(self):
        """Get episode metadata."""
        r = requests.get(f"{self.base_url}/state")
        r.raise_for_status()
        return r.json()
