import copy
import threading

# Raw reward values — used internally
_REWARD_ALL_PASS = 100.0
_REWARD_CRASH    = -20.0
_REWARD_MIN      = -20.0
_REWARD_MAX      = 100.0

_EXEC_TIMEOUT    = 5   # seconds — per test case


def _run_in_thread(fn, args, result_holder, timeout):
    """Run fn(*args) in a daemon thread; stores result or exception."""
    def target():
        try:
            result_holder["value"] = fn(*args)
        except Exception as exc:
            result_holder["error"] = exc

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise TimeoutError(f"execution timed out after {timeout}s")


def grade(submitted_code: str, task: dict):
    """
    Run submitted_code against every test case in task.
    Returns (passed, total, results, crashed).

    Each test case is run in a daemon thread with a timeout to prevent
    infinite loops from hanging the server.
    Inputs are deep-copied before each call so mutable arguments
    (lists, dicts) are never modified in the task definition.
    """
    test_cases    = task["test_cases"]
    function_name = task["function_name"]

    total   = len(test_cases)
    passed  = 0
    results = []
    crashed = False

    for i, test in enumerate(test_cases):
        try:
            namespace = {}
            exec(submitted_code, namespace)

            if function_name not in namespace:
                results.append(f"test {i+1}: FAIL — function '{function_name}' not found")
                continue

            fn       = namespace[function_name]
            args     = copy.deepcopy(test["input"])
            expected = test["expected"]

            # Run with timeout to guard against infinite loops
            result_holder = {}
            _run_in_thread(fn, args, result_holder, _EXEC_TIMEOUT)

            if "error" in result_holder:
                raise result_holder["error"]

            actual = result_holder["value"]

            if actual == expected:
                passed += 1
                results.append(f"test {i+1}: PASS — got {actual}")
            else:
                results.append(f"test {i+1}: FAIL — expected {expected}, got {actual}")

        except TimeoutError as e:
            crashed = True
            results.append(f"test {i+1}: ERROR — {e}")

        except SyntaxError as e:
            crashed = True
            results.append(f"test {i+1}: ERROR — syntax error: {e.msg}")
            break

        except Exception as e:
            crashed = True
            results.append(f"test {i+1}: ERROR — {type(e).__name__}: {e}")

    return passed, total, results, crashed


def calculate_reward(passed: int, total: int, crashed: bool):
    """
    Returns (normalised_reward, score).

    normalised_reward: [0.0, 1.0] — what the API exposes as 'reward'
    score            : [0.0, 1.0] — passed / total
    """
    score = passed / total if total > 0 else 0.0

    if crashed and passed == 0:
        raw = _REWARD_CRASH
    elif passed == total:
        raw = _REWARD_ALL_PASS
    else:
        raw = score * 100

    normalised = (raw - _REWARD_MIN) / (_REWARD_MAX - _REWARD_MIN)
    # Ensure reward is strictly within (0.0, 1.0) for platform validation.
    # Map [0.0, 1.0] -> [0.05, 0.95]
    normalised = 0.05 + 0.90 * normalised
    normalised = max(0.001, min(0.999, normalised))   # double-check clamp

    return normalised, score
