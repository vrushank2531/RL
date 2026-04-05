import copy

# Raw reward values — used internally
_REWARD_ALL_PASS = 100.0
_REWARD_CRASH    = -20.0
_REWARD_MIN      = -20.0
_REWARD_MAX      = 100.0


def grade(submitted_code: str, task: dict):
    """
    Run submitted_code against every test case in task.
    Returns (passed, total, results, crashed).

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
            actual   = fn(*args)
            expected = test["expected"]

            if actual == expected:
                passed += 1
                results.append(f"test {i+1}: PASS — got {actual}")
            else:
                results.append(f"test {i+1}: FAIL — expected {expected}, got {actual}")

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
    Returns (raw_reward, normalised_score).

    raw_reward     : [-20.0, 100.0]  — for internal use / logging
    normalised_score: [0.0,  1.0]   — what the API exposes as 'reward'
    """
    score = passed / total if total > 0 else 0.0

    if crashed and passed == 0:
        raw = _REWARD_CRASH
    elif passed == total:
        raw = _REWARD_ALL_PASS
    else:
        raw = score * 100

    normalised = (raw - _REWARD_MIN) / (_REWARD_MAX - _REWARD_MIN)
    normalised = max(0.0, min(1.0, normalised))   # clamp

    return normalised, score
