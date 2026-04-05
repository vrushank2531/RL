TASKS = {

    # ── EASY ──────────────────────────────────────────────────────────────────

    1: {
        "difficulty": "easy",
        "description": "Fix the syntax error — this function is missing a colon",
        "broken_code": (
            "def add_numbers(a, b)\n"
            "    return a + b"
        ),
        "function_name": "add_numbers",
        "test_cases": [
            {"input": (2,  3),  "expected": 5},
            {"input": (0,  0),  "expected": 0},
            {"input": (-1, 1),  "expected": 0},
        ],
    },

    2: {
        "difficulty": "easy",
        "description": (
            "Fix the logic error — this function should return "
            "the MAXIMUM value, not the minimum"
        ),
        "broken_code": (
            "def get_max(a, b):\n"
            "    return a if a < b else b"
        ),
        "function_name": "get_max",
        "test_cases": [
            {"input": (5, 3), "expected": 5},
            {"input": (1, 9), "expected": 9},
            {"input": (4, 4), "expected": 4},
        ],
    },

    # ── MEDIUM ─────────────────────────────────────────────────────────────────

    3: {
        "difficulty": "medium",
        "description": (
            "Fix the algorithm error — bubble sort should "
            "swap elements correctly using a temp variable or tuple swap"
        ),
        "broken_code": (
            "def bubble_sort(arr):\n"
            "    for i in range(len(arr)):\n"
            "        for j in range(len(arr) - 1):\n"
            "            if arr[j] > arr[j + 1]:\n"
            "                arr[j] = arr[j + 1]\n"
            "    return arr"
        ),
        "function_name": "bubble_sort",
        "test_cases": [
            {"input": ([3, 1, 2],),       "expected": [1, 2, 3]},
            {"input": ([5, 4, 3, 2, 1],), "expected": [1, 2, 3, 4, 5]},
            {"input": ([1],),             "expected": [1]},
            {"input": ([2, 2, 1],),       "expected": [1, 2, 2]},
        ],
    },

    4: {
        "difficulty": "medium",
        "description": (
            "Fix the recursion bug — fibonacci returns wrong values "
            "because the base cases are swapped"
        ),
        "broken_code": (
            "def fibonacci(n):\n"
            "    if n == 0:\n"
            "        return 1\n"
            "    if n == 1:\n"
            "        return 0\n"
            "    return fibonacci(n - 1) + fibonacci(n - 2)"
        ),
        "function_name": "fibonacci",
        "test_cases": [
            {"input": (0,),  "expected": 0},
            {"input": (1,),  "expected": 1},
            {"input": (6,),  "expected": 8},
            {"input": (10,), "expected": 55},
        ],
    },

    5: {
        "difficulty": "medium",
        "description": (
            "Fix the off-by-one error in binary search — "
            "it misses the last element in any list"
        ),
        "broken_code": (
            "def binary_search(arr, target):\n"
            "    low, high = 0, len(arr) - 2\n"
            "    while low <= high:\n"
            "        mid = (low + high) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            low = mid + 1\n"
            "        else:\n"
            "            high = mid - 1\n"
            "    return -1"
        ),
        "function_name": "binary_search",
        "test_cases": [
            {"input": ([1, 3, 5, 7, 9], 9), "expected": 4},
            {"input": ([1, 3, 5, 7, 9], 1), "expected": 0},
            {"input": ([1, 3, 5, 7, 9], 5), "expected": 2},
            {"input": ([1, 3, 5, 7, 9], 4), "expected": -1},
        ],
    },

    # ── HARD ───────────────────────────────────────────────────────────────────

    6: {
        "difficulty": "hard",
        "description": (
            "Fix the dynamic programming bug — longest common subsequence "
            "is returning the wrong length because the DP table is not "
            "filled in correctly when characters match"
        ),
        "broken_code": (
            "def lcs(s1, s2):\n"
            "    m, n = len(s1), len(s2)\n"
            "    dp = [[0] * (n + 1) for _ in range(m + 1)]\n"
            "    for i in range(1, m + 1):\n"
            "        for j in range(1, n + 1):\n"
            "            if s1[i-1] == s2[j-1]:\n"
            "                dp[i][j] = dp[i-1][j-1]\n"
            "            else:\n"
            "                dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n"
            "    return dp[m][n]"
        ),
        "function_name": "lcs",
        "test_cases": [
            {"input": ("abcde", "ace"),    "expected": 3},
            {"input": ("abc",   "abc"),    "expected": 3},
            {"input": ("abc",   "def"),    "expected": 0},
            {"input": ("AGGTAB", "GXTXAYB"), "expected": 4},
        ],
    },

    7: {
        "difficulty": "hard",
        "description": (
            "Fix the string parsing bug — is_balanced should return True "
            "only when every opening bracket has a matching closing bracket "
            "in the correct order, but it incorrectly handles mismatched pairs"
        ),
        "broken_code": (
            "def is_balanced(s):\n"
            "    stack = []\n"
            "    pairs = {')': '(', ']': '[', '}': '{'}\n"
            "    for ch in s:\n"
            "        if ch in '([{':\n"
            "            stack.append(ch)\n"
            "        elif ch in ')]}':\n"
            "            if stack and stack[-1] == pairs[ch]:\n"
            "                stack.append(ch)\n"
            "            else:\n"
            "                return False\n"
            "    return len(stack) == 0"
        ),
        "function_name": "is_balanced",
        "test_cases": [
            {"input": ("([]{})",),   "expected": True},
            {"input": ("([)]",),     "expected": False},
            {"input": ("",),         "expected": True},
            {"input": ("{[()]}",),   "expected": True},
            {"input": ("(((",),      "expected": False},
        ],
    },

}
