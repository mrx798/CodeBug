"""
Synthetic bug corpus — 50+ Python code snippets with bugs across 3 categories.
Each entry includes buggy code, fixed code, test cases, and metadata.
"""
from __future__ import annotations
from models import BugEntry, BugType, Difficulty, TestCase, VulnerabilityType

# ---------------------------------------------------------------------------
# SYNTAX BUGS (Easy) — 18 entries
# ---------------------------------------------------------------------------
_SYNTAX_BUGS: list[dict] = [
    {
        "id": "syntax_001",
        "domain": "math",
        "bug_description": "Missing colon after function definition",
        "buggy_code": "def add(a, b)\n    return a + b",
        "fixed_code": "def add(a, b):\n    return a + b",
        "error_message": "SyntaxError: expected ':'",
        "hints": ["Check the function definition syntax"],
        "test_cases": [
            {"input": [1, 2], "expected_output": 3, "description": "basic add"},
            {"input": [-1, 1], "expected_output": 0, "description": "neg+pos"},
            {"input": [0, 0], "expected_output": 0, "description": "zeros"},
        ],
    },
    {
        "id": "syntax_002",
        "domain": "string",
        "bug_description": "Unclosed string literal",
        "buggy_code": "def greet(name):\n    return 'Hello, ' + name + '!",
        "fixed_code": "def greet(name):\n    return 'Hello, ' + name + '!'",
        "error_message": "SyntaxError: unterminated string literal",
        "hints": ["Check quote marks"],
        "test_cases": [
            {"input": ["Alice"], "expected_output": "Hello, Alice!", "description": "basic"},
            {"input": [""], "expected_output": "Hello, !", "description": "empty"},
            {"input": ["Bob"], "expected_output": "Hello, Bob!", "description": "another"},
        ],
    },
    {
        "id": "syntax_003",
        "domain": "list",
        "bug_description": "NameError — undefined variable",
        "buggy_code": "def double_list(lst):\n    return [x * 2 for x in lst]\n\nresult = double_list(my_list)",
        "fixed_code": "def double_list(lst):\n    return [x * 2 for x in lst]\n\nmy_list = [1, 2, 3]\nresult = double_list(my_list)",
        "error_message": "NameError: name 'my_list' is not defined",
        "hints": ["A variable is used before being defined"],
        "test_cases": [
            {"input": [[1, 2, 3]], "expected_output": [2, 4, 6], "description": "basic"},
            {"input": [[0]], "expected_output": [0], "description": "zero"},
            {"input": [[-1, 5]], "expected_output": [-2, 10], "description": "mixed"},
        ],
    },
    {
        "id": "syntax_004",
        "domain": "math",
        "bug_description": "TypeError — wrong argument count",
        "buggy_code": "def multiply(a, b):\n    return a * b\n\nresult = multiply(3)",
        "fixed_code": "def multiply(a, b):\n    return a * b\n\nresult = multiply(3, 2)",
        "error_message": "TypeError: multiply() missing 1 required positional argument: 'b'",
        "hints": ["Check function call arguments"],
        "test_cases": [
            {"input": [3, 2], "expected_output": 6, "description": "basic"},
            {"input": [0, 5], "expected_output": 0, "description": "zero"},
            {"input": [-2, 3], "expected_output": -6, "description": "negative"},
        ],
    },
    {
        "id": "syntax_005",
        "domain": "dict",
        "bug_description": "Missing bracket in dictionary",
        "buggy_code": "def make_person(name, age):\n    return {'name': name, 'age': age",
        "fixed_code": "def make_person(name, age):\n    return {'name': name, 'age': age}",
        "error_message": "SyntaxError: unexpected EOF while parsing",
        "hints": ["Check brackets and braces"],
        "test_cases": [
            {"input": ["Alice", 30], "expected_output": {"name": "Alice", "age": 30}, "description": "basic"},
            {"input": ["Bob", 0], "expected_output": {"name": "Bob", "age": 0}, "description": "zero age"},
            {"input": ["", 99], "expected_output": {"name": "", "age": 99}, "description": "empty name"},
        ],
    },
    {
        "id": "syntax_006",
        "domain": "math",
        "bug_description": "IndentationError in function body",
        "buggy_code": "def square(n):\nreturn n * n",
        "fixed_code": "def square(n):\n    return n * n",
        "error_message": "IndentationError: expected an indented block",
        "hints": ["Check indentation"],
        "test_cases": [
            {"input": [4], "expected_output": 16, "description": "basic"},
            {"input": [0], "expected_output": 0, "description": "zero"},
            {"input": [-3], "expected_output": 9, "description": "negative"},
        ],
    },
    {
        "id": "syntax_007",
        "domain": "string",
        "bug_description": "Using = instead of == in comparison",
        "buggy_code": "def is_empty(s):\n    if s = '':\n        return True\n    return False",
        "fixed_code": "def is_empty(s):\n    if s == '':\n        return True\n    return False",
        "error_message": "SyntaxError: invalid syntax",
        "hints": ["Check comparison operator"],
        "test_cases": [
            {"input": [""], "expected_output": True, "description": "empty"},
            {"input": ["hi"], "expected_output": False, "description": "non-empty"},
            {"input": [" "], "expected_output": False, "description": "space"},
        ],
    },
    {
        "id": "syntax_008",
        "domain": "list",
        "bug_description": "Missing parenthesis in print call",
        "buggy_code": "def show_items(items):\n    for item in items:\n        print(item\n    return len(items)",
        "fixed_code": "def show_items(items):\n    for item in items:\n        print(item)\n    return len(items)",
        "error_message": "SyntaxError: unexpected EOF while parsing",
        "hints": ["Check parentheses"],
        "test_cases": [
            {"input": [[1, 2]], "expected_output": 2, "description": "two items"},
            {"input": [[]], "expected_output": 0, "description": "empty"},
            {"input": [["a"]], "expected_output": 1, "description": "one item"},
        ],
    },
    {
        "id": "syntax_009",
        "domain": "math",
        "bug_description": "TypeError: unsupported operand types",
        "buggy_code": "def add_to_string(n):\n    return '10' + n",
        "fixed_code": "def add_to_string(n):\n    return '10' + str(n)",
        "error_message": "TypeError: can only concatenate str (not \"int\") to str",
        "hints": ["Check type compatibility"],
        "test_cases": [
            {"input": [5], "expected_output": "105", "description": "basic"},
            {"input": [0], "expected_output": "100", "description": "zero"},
            {"input": [99], "expected_output": "1099", "description": "large"},
        ],
    },
    {
        "id": "syntax_010",
        "domain": "list",
        "bug_description": "IndexError — off by one on list access",
        "buggy_code": "def get_last(lst):\n    return lst[len(lst)]",
        "fixed_code": "def get_last(lst):\n    return lst[len(lst) - 1]",
        "error_message": "IndexError: list index out of range",
        "hints": ["Python lists are 0-indexed"],
        "test_cases": [
            {"input": [[1, 2, 3]], "expected_output": 3, "description": "basic"},
            {"input": [[42]], "expected_output": 42, "description": "single"},
            {"input": [["a", "b"]], "expected_output": "b", "description": "strings"},
        ],
    },
    {
        "id": "syntax_011",
        "domain": "string",
        "bug_description": "Missing f-string prefix",
        "buggy_code": "def format_msg(name, count):\n    return 'Hello {name}, you have {count} items'",
        "fixed_code": "def format_msg(name, count):\n    return f'Hello {name}, you have {count} items'",
        "error_message": "",
        "hints": ["Check string formatting"],
        "test_cases": [
            {"input": ["Alice", 3], "expected_output": "Hello Alice, you have 3 items", "description": "basic"},
            {"input": ["Bob", 0], "expected_output": "Hello Bob, you have 0 items", "description": "zero"},
            {"input": ["Eve", 1], "expected_output": "Hello Eve, you have 1 items", "description": "one"},
        ],
    },
    {
        "id": "syntax_012",
        "domain": "math",
        "bug_description": "Missing return statement",
        "buggy_code": "def absolute(n):\n    if n < 0:\n        result = -n\n    else:\n        result = n",
        "fixed_code": "def absolute(n):\n    if n < 0:\n        result = -n\n    else:\n        result = n\n    return result",
        "error_message": "",
        "hints": ["Check if the function returns a value"],
        "test_cases": [
            {"input": [-5], "expected_output": 5, "description": "negative"},
            {"input": [3], "expected_output": 3, "description": "positive"},
            {"input": [0], "expected_output": 0, "description": "zero"},
        ],
    },
    {
        "id": "syntax_013",
        "domain": "list",
        "bug_description": "Using append instead of extend",
        "buggy_code": "def flatten(nested):\n    result = []\n    for sublist in nested:\n        result.append(sublist)\n    return result",
        "fixed_code": "def flatten(nested):\n    result = []\n    for sublist in nested:\n        result.extend(sublist)\n    return result",
        "error_message": "",
        "hints": ["append vs extend"],
        "test_cases": [
            {"input": [[[1, 2], [3]]], "expected_output": [1, 2, 3], "description": "basic"},
            {"input": [[[], [1]]], "expected_output": [1], "description": "empty sub"},
            {"input": [[[5]]], "expected_output": [5], "description": "single"},
        ],
    },
    {
        "id": "syntax_014",
        "domain": "dict",
        "bug_description": "KeyError due to wrong key name",
        "buggy_code": "def get_name(person):\n    return person['username']",
        "fixed_code": "def get_name(person):\n    return person['name']",
        "error_message": "KeyError: 'username'",
        "hints": ["Check dictionary keys"],
        "test_cases": [
            {"input": [{"name": "Alice"}], "expected_output": "Alice", "description": "basic"},
            {"input": [{"name": ""}], "expected_output": "", "description": "empty"},
            {"input": [{"name": "Bob"}], "expected_output": "Bob", "description": "another"},
        ],
    },
    {
        "id": "syntax_015",
        "domain": "math",
        "bug_description": "Calling method on None",
        "buggy_code": "def sorted_list(lst):\n    result = lst.sort()\n    return result.copy()",
        "fixed_code": "def sorted_list(lst):\n    result = sorted(lst)\n    return result.copy()",
        "error_message": "AttributeError: 'NoneType' object has no attribute 'copy'",
        "hints": ["list.sort() returns None"],
        "test_cases": [
            {"input": [[3, 1, 2]], "expected_output": [1, 2, 3], "description": "basic"},
            {"input": [[1]], "expected_output": [1], "description": "single"},
            {"input": [[5, 4, 3, 2, 1]], "expected_output": [1, 2, 3, 4, 5], "description": "reverse"},
        ],
    },
    {
        "id": "syntax_016",
        "domain": "string",
        "bug_description": "Wrong method name — strip vs trip",
        "buggy_code": "def clean(s):\n    return s.trip()",
        "fixed_code": "def clean(s):\n    return s.strip()",
        "error_message": "AttributeError: 'str' object has no attribute 'trip'",
        "hints": ["Check the method name"],
        "test_cases": [
            {"input": ["  hi  "], "expected_output": "hi", "description": "spaces"},
            {"input": ["hello"], "expected_output": "hello", "description": "clean"},
            {"input": [" "], "expected_output": "", "description": "just space"},
        ],
    },
    {
        "id": "syntax_017",
        "domain": "math",
        "bug_description": "Division by zero not handled",
        "buggy_code": "def safe_divide(a, b):\n    return a / b",
        "fixed_code": "def safe_divide(a, b):\n    if b == 0:\n        return 0\n    return a / b",
        "error_message": "ZeroDivisionError: division by zero",
        "hints": ["Handle the case when divisor is zero"],
        "test_cases": [
            {"input": [10, 2], "expected_output": 5.0, "description": "basic"},
            {"input": [0, 5], "expected_output": 0.0, "description": "zero num"},
            {"input": [1, 0], "expected_output": 0, "description": "div by zero"},
        ],
    },
    {
        "id": "syntax_018",
        "domain": "list",
        "bug_description": "Mutable default argument",
        "buggy_code": "def append_item(item, lst=[]):\n    lst.append(item)\n    return lst",
        "fixed_code": "def append_item(item, lst=None):\n    if lst is None:\n        lst = []\n    lst.append(item)\n    return lst",
        "error_message": "",
        "hints": ["Mutable default arguments are shared across calls"],
        "test_cases": [
            {"input": [1], "expected_output": [1], "description": "first call"},
            {"input": [2], "expected_output": [2], "description": "second call independent"},
            {"input": [3, [10]], "expected_output": [10, 3], "description": "with existing list"},
        ],
    },
]

# ---------------------------------------------------------------------------
# LOGIC BUGS (Medium) — 18 entries
# ---------------------------------------------------------------------------
_LOGIC_BUGS: list[dict] = [
    {
        "id": "logic_001",
        "domain": "sorting",
        "bug_description": "Off-by-one in bubble sort — range should be len-1",
        "buggy_code": "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(n - 1):\n            if arr[j] > arr[j + 1]:\n                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n    return arr",
        "fixed_code": "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(n - 1 - i):\n            if arr[j] > arr[j + 1]:\n                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n    return arr",
        "hints": ["The inner loop does unnecessary comparisons"],
        "test_cases": [
            {"input": [[3, 1, 2]], "expected_output": [1, 2, 3], "description": "basic"},
            {"input": [[1]], "expected_output": [1], "description": "single"},
            {"input": [[5, 4, 3, 2, 1]], "expected_output": [1, 2, 3, 4, 5], "description": "reversed"},
            {"input": [[1, 2, 3]], "expected_output": [1, 2, 3], "description": "sorted"},
            {"input": [[2, 2, 1]], "expected_output": [1, 2, 2], "description": "duplicates"},
        ],
    },
    {
        "id": "logic_002",
        "domain": "search",
        "bug_description": "Binary search uses wrong midpoint update",
        "buggy_code": "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid\n        else:\n            hi = mid\n    return -1",
        "fixed_code": "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1",
        "hints": ["Check how lo and hi are updated"],
        "test_cases": [
            {"input": [[1, 2, 3, 4, 5], 3], "expected_output": 2, "description": "found middle"},
            {"input": [[1, 2, 3], 4], "expected_output": -1, "description": "not found"},
            {"input": [[10], 10], "expected_output": 0, "description": "single element"},
            {"input": [[1, 3, 5, 7], 1], "expected_output": 0, "description": "first"},
            {"input": [[1, 3, 5, 7], 7], "expected_output": 3, "description": "last"},
        ],
    },
    {
        "id": "logic_003",
        "domain": "math",
        "bug_description": "Fibonacci uses wrong base cases",
        "buggy_code": "def fibonacci(n):\n    if n <= 0:\n        return 0\n    if n == 1:\n        return 0\n    return fibonacci(n - 1) + fibonacci(n - 2)",
        "fixed_code": "def fibonacci(n):\n    if n <= 0:\n        return 0\n    if n == 1:\n        return 1\n    return fibonacci(n - 1) + fibonacci(n - 2)",
        "hints": ["Check the base case values"],
        "test_cases": [
            {"input": [0], "expected_output": 0, "description": "zero"},
            {"input": [1], "expected_output": 1, "description": "one"},
            {"input": [5], "expected_output": 5, "description": "five"},
            {"input": [7], "expected_output": 13, "description": "seven"},
            {"input": [10], "expected_output": 55, "description": "ten"},
        ],
    },
    {
        "id": "logic_004",
        "domain": "string",
        "bug_description": "Palindrome check uses wrong comparison index",
        "buggy_code": "def is_palindrome(s):\n    s = s.lower()\n    for i in range(len(s) // 2):\n        if s[i] != s[len(s) - i]:\n            return False\n    return True",
        "fixed_code": "def is_palindrome(s):\n    s = s.lower()\n    for i in range(len(s) // 2):\n        if s[i] != s[len(s) - 1 - i]:\n            return False\n    return True",
        "hints": ["Check the index calculation for the right side"],
        "test_cases": [
            {"input": ["racecar"], "expected_output": True, "description": "palindrome"},
            {"input": ["hello"], "expected_output": False, "description": "not palindrome"},
            {"input": ["a"], "expected_output": True, "description": "single char"},
            {"input": ["Aba"], "expected_output": True, "description": "case insensitive"},
            {"input": ["ab"], "expected_output": False, "description": "two chars"},
        ],
    },
    {
        "id": "logic_005",
        "domain": "math",
        "bug_description": "Max finder starts with 0 instead of first element",
        "buggy_code": "def find_max(lst):\n    max_val = 0\n    for x in lst:\n        if x > max_val:\n            max_val = x\n    return max_val",
        "fixed_code": "def find_max(lst):\n    max_val = lst[0]\n    for x in lst:\n        if x > max_val:\n            max_val = x\n    return max_val",
        "hints": ["What if all values are negative?"],
        "test_cases": [
            {"input": [[1, 3, 2]], "expected_output": 3, "description": "positive"},
            {"input": [[-5, -1, -3]], "expected_output": -1, "description": "negatives"},
            {"input": [[42]], "expected_output": 42, "description": "single"},
            {"input": [[-10, 0, 10]], "expected_output": 10, "description": "mixed"},
            {"input": [[7, 7, 7]], "expected_output": 7, "description": "all same"},
        ],
    },
    {
        "id": "logic_006",
        "domain": "list",
        "bug_description": "Reverse function only reverses half",
        "buggy_code": "def reverse_list(lst):\n    result = lst[:]\n    n = len(result)\n    for i in range(n // 2):\n        result[i] = result[n - 1 - i]\n    return result",
        "fixed_code": "def reverse_list(lst):\n    result = lst[:]\n    n = len(result)\n    for i in range(n // 2):\n        result[i], result[n - 1 - i] = result[n - 1 - i], result[i]\n    return result",
        "hints": ["The swap is not symmetric"],
        "test_cases": [
            {"input": [[1, 2, 3]], "expected_output": [3, 2, 1], "description": "basic"},
            {"input": [[1]], "expected_output": [1], "description": "single"},
            {"input": [[1, 2, 3, 4]], "expected_output": [4, 3, 2, 1], "description": "even len"},
            {"input": [["a", "b"]], "expected_output": ["b", "a"], "description": "strings"},
            {"input": [[]], "expected_output": [], "description": "empty"},
        ],
    },
    {
        "id": "logic_007",
        "domain": "math",
        "bug_description": "Factorial uses wrong base case — returns 0 instead of 1",
        "buggy_code": "def factorial(n):\n    if n == 0:\n        return 0\n    return n * factorial(n - 1)",
        "fixed_code": "def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n - 1)",
        "hints": ["What is 0!?"],
        "test_cases": [
            {"input": [0], "expected_output": 1, "description": "zero"},
            {"input": [1], "expected_output": 1, "description": "one"},
            {"input": [5], "expected_output": 120, "description": "five"},
            {"input": [3], "expected_output": 6, "description": "three"},
            {"input": [7], "expected_output": 5040, "description": "seven"},
        ],
    },
    {
        "id": "logic_008",
        "domain": "string",
        "bug_description": "Word counter splits on wrong delimiter",
        "buggy_code": "def count_words(text):\n    return len(text.split(','))",
        "fixed_code": "def count_words(text):\n    return len(text.split())",
        "hints": ["Words are separated by spaces, not commas"],
        "test_cases": [
            {"input": ["hello world"], "expected_output": 2, "description": "two words"},
            {"input": ["one"], "expected_output": 1, "description": "one word"},
            {"input": ["a b c d"], "expected_output": 4, "description": "four words"},
            {"input": ["hello  world"], "expected_output": 2, "description": "extra spaces"},
            {"input": [""], "expected_output": 0, "description": "empty string"},
        ],
    },
    {
        "id": "logic_009",
        "domain": "data",
        "bug_description": "Average calculation uses integer division",
        "buggy_code": "def average(numbers):\n    return sum(numbers) // len(numbers)",
        "fixed_code": "def average(numbers):\n    return sum(numbers) / len(numbers)",
        "hints": ["Check division type"],
        "test_cases": [
            {"input": [[1, 2, 3]], "expected_output": 2.0, "description": "basic"},
            {"input": [[1, 2]], "expected_output": 1.5, "description": "non-integer result"},
            {"input": [[10]], "expected_output": 10.0, "description": "single"},
            {"input": [[0, 0, 0]], "expected_output": 0.0, "description": "zeros"},
            {"input": [[1, 2, 3, 4]], "expected_output": 2.5, "description": "four nums"},
        ],
    },
    {
        "id": "logic_010",
        "domain": "list",
        "bug_description": "Remove duplicates loses order",
        "buggy_code": "def unique(lst):\n    return list(set(lst))",
        "fixed_code": "def unique(lst):\n    seen = set()\n    result = []\n    for x in lst:\n        if x not in seen:\n            seen.add(x)\n            result.append(x)\n    return result",
        "hints": ["Sets don't preserve insertion order"],
        "test_cases": [
            {"input": [[1, 2, 2, 3]], "expected_output": [1, 2, 3], "description": "basic"},
            {"input": [[3, 1, 3, 1]], "expected_output": [3, 1], "description": "order matters"},
            {"input": [[1]], "expected_output": [1], "description": "single"},
            {"input": [[5, 5, 5]], "expected_output": [5], "description": "all dupes"},
            {"input": [[1, 2, 3]], "expected_output": [1, 2, 3], "description": "no dupes"},
        ],
    },
    {
        "id": "logic_011",
        "domain": "math",
        "bug_description": "Power function uses addition instead of multiplication",
        "buggy_code": "def power(base, exp):\n    result = 1\n    for _ in range(exp):\n        result += base\n    return result",
        "fixed_code": "def power(base, exp):\n    result = 1\n    for _ in range(exp):\n        result *= base\n    return result",
        "hints": ["Check the accumulation operator"],
        "test_cases": [
            {"input": [2, 3], "expected_output": 8, "description": "2^3"},
            {"input": [5, 0], "expected_output": 1, "description": "x^0"},
            {"input": [3, 2], "expected_output": 9, "description": "3^2"},
            {"input": [1, 10], "expected_output": 1, "description": "1^n"},
            {"input": [2, 10], "expected_output": 1024, "description": "2^10"},
        ],
    },
    {
        "id": "logic_012",
        "domain": "string",
        "bug_description": "Capitalize first letter lowercases wrong part",
        "buggy_code": "def capitalize_first(s):\n    if not s:\n        return s\n    return s[0].lower() + s[1:]",
        "fixed_code": "def capitalize_first(s):\n    if not s:\n        return s\n    return s[0].upper() + s[1:]",
        "hints": ["upper vs lower"],
        "test_cases": [
            {"input": ["hello"], "expected_output": "Hello", "description": "basic"},
            {"input": ["Hello"], "expected_output": "Hello", "description": "already cap"},
            {"input": ["a"], "expected_output": "A", "description": "single"},
            {"input": ["123"], "expected_output": "123", "description": "digit"},
            {"input": [""], "expected_output": "", "description": "empty"},
        ],
    },
    {
        "id": "logic_013",
        "domain": "math",
        "bug_description": "GCD uses subtraction instead of modulo",
        "buggy_code": "def gcd(a, b):\n    while b:\n        a, b = b, a - b\n    return a",
        "fixed_code": "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a",
        "hints": ["Euclidean algorithm uses modulo"],
        "test_cases": [
            {"input": [12, 8], "expected_output": 4, "description": "basic"},
            {"input": [7, 3], "expected_output": 1, "description": "coprime"},
            {"input": [100, 25], "expected_output": 25, "description": "divisible"},
            {"input": [1, 1], "expected_output": 1, "description": "ones"},
            {"input": [48, 18], "expected_output": 6, "description": "larger"},
        ],
    },
    {
        "id": "logic_014",
        "domain": "list",
        "bug_description": "Zip function truncates — should pad with None",
        "buggy_code": "def zip_lists(a, b):\n    result = []\n    for i in range(min(len(a), len(b))):\n        result.append((a[i], b[i]))\n    return result",
        "fixed_code": "def zip_lists(a, b):\n    result = []\n    for i in range(max(len(a), len(b))):\n        val_a = a[i] if i < len(a) else None\n        val_b = b[i] if i < len(b) else None\n        result.append((val_a, val_b))\n    return result",
        "hints": ["Should handle unequal length lists"],
        "test_cases": [
            {"input": [[1, 2], ["a", "b"]], "expected_output": [[1, "a"], [2, "b"]], "description": "equal"},
            {"input": [[1], ["a", "b"]], "expected_output": [[1, "a"], [None, "b"]], "description": "first shorter"},
            {"input": [[1, 2], ["a"]], "expected_output": [[1, "a"], [2, None]], "description": "second shorter"},
            {"input": [[], [1]], "expected_output": [[None, 1]], "description": "empty first"},
            {"input": [[], []], "expected_output": [], "description": "both empty"},
        ],
    },
    {
        "id": "logic_015",
        "domain": "data",
        "bug_description": "Count occurrences uses wrong comparison",
        "buggy_code": "def count_value(lst, target):\n    count = 0\n    for x in lst:\n        if x != target:\n            count += 1\n    return count",
        "fixed_code": "def count_value(lst, target):\n    count = 0\n    for x in lst:\n        if x == target:\n            count += 1\n    return count",
        "hints": ["Check the comparison operator"],
        "test_cases": [
            {"input": [[1, 2, 1, 3], 1], "expected_output": 2, "description": "basic"},
            {"input": [[1, 1, 1], 1], "expected_output": 3, "description": "all match"},
            {"input": [[1, 2, 3], 4], "expected_output": 0, "description": "none match"},
            {"input": [[], 1], "expected_output": 0, "description": "empty"},
            {"input": [["a", "b", "a"], "a"], "expected_output": 2, "description": "strings"},
        ],
    },
    {
        "id": "logic_016",
        "domain": "math",
        "bug_description": "Is prime returns wrong value for 1",
        "buggy_code": "def is_prime(n):\n    if n < 2:\n        return True\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True",
        "fixed_code": "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True",
        "hints": ["1 is not a prime number"],
        "test_cases": [
            {"input": [1], "expected_output": False, "description": "one"},
            {"input": [2], "expected_output": True, "description": "two"},
            {"input": [7], "expected_output": True, "description": "prime"},
            {"input": [4], "expected_output": False, "description": "composite"},
            {"input": [0], "expected_output": False, "description": "zero"},
        ],
    },
    {
        "id": "logic_017",
        "domain": "list",
        "bug_description": "Intersection returns union instead",
        "buggy_code": "def intersect(a, b):\n    return list(set(a) | set(b))",
        "fixed_code": "def intersect(a, b):\n    return list(set(a) & set(b))",
        "hints": ["Union vs intersection"],
        "test_cases": [
            {"input": [[1, 2, 3], [2, 3, 4]], "expected_output": [2, 3], "description": "basic"},
            {"input": [[1], [2]], "expected_output": [], "description": "disjoint"},
            {"input": [[1, 2], [1, 2]], "expected_output": [1, 2], "description": "same"},
            {"input": [[], [1]], "expected_output": [], "description": "empty"},
            {"input": [[1, 1, 2], [1]], "expected_output": [1], "description": "dupes"},
        ],
    },
    {
        "id": "logic_018",
        "domain": "string",
        "bug_description": "Vowel counter counts consonants instead",
        "buggy_code": "def count_vowels(s):\n    vowels = 'aeiouAEIOU'\n    count = 0\n    for ch in s:\n        if ch not in vowels:\n            count += 1\n    return count",
        "fixed_code": "def count_vowels(s):\n    vowels = 'aeiouAEIOU'\n    count = 0\n    for ch in s:\n        if ch in vowels:\n            count += 1\n    return count",
        "hints": ["Check the membership test direction"],
        "test_cases": [
            {"input": ["hello"], "expected_output": 2, "description": "basic"},
            {"input": ["aeiou"], "expected_output": 5, "description": "all vowels"},
            {"input": ["xyz"], "expected_output": 0, "description": "no vowels"},
            {"input": ["AeIoU"], "expected_output": 5, "description": "uppercase"},
            {"input": [""], "expected_output": 0, "description": "empty"},
        ],
    },
]

# ---------------------------------------------------------------------------
# SECURITY BUGS (Hard) — 16 entries
# ---------------------------------------------------------------------------
_SECURITY_BUGS: list[dict] = [
    {
        "id": "security_001",
        "domain": "database",
        "bug_description": "SQL injection via string formatting",
        "vulnerability_type": "sql_injection",
        "buggy_code": "import sqlite3\n\ndef get_user(db, username):\n    query = f\"SELECT * FROM users WHERE name = '{username}'\"\n    return db.execute(query).fetchone()",
        "fixed_code": "import sqlite3\n\ndef get_user(db, username):\n    query = \"SELECT * FROM users WHERE name = ?\"\n    return db.execute(query, (username,)).fetchone()",
        "hints": ["User input is directly interpolated into SQL"],
        "security_concepts": ["sql injection", "parameterized query", "prepared statement", "input sanitization", "bobby tables"],
        "test_cases": [
            {"input": ["test_user"], "expected_output": "parameterized", "description": "uses params"},
            {"input": ["'; DROP TABLE--"], "expected_output": "safe", "description": "injection safe"},
            {"input": ["normal"], "expected_output": "parameterized", "description": "normal safe"},
        ],
    },
    {
        "id": "security_002",
        "domain": "api",
        "bug_description": "Hardcoded API key in source code",
        "vulnerability_type": "hardcoded_secret",
        "buggy_code": "import requests\n\nAPI_KEY = 'sk-abc123secret456key789'\n\ndef fetch_data(endpoint):\n    headers = {'Authorization': f'Bearer {API_KEY}'}\n    return requests.get(endpoint, headers=headers).json()",
        "fixed_code": "import os\nimport requests\n\ndef fetch_data(endpoint):\n    api_key = os.environ.get('API_KEY')\n    if not api_key:\n        raise ValueError('API_KEY environment variable not set')\n    headers = {'Authorization': f'Bearer {api_key}'}\n    return requests.get(endpoint, headers=headers).json()",
        "hints": ["Credentials should never be hardcoded"],
        "security_concepts": ["hardcoded credentials", "secret management", "environment variable", "credential rotation", "source code exposure"],
        "test_cases": [
            {"input": ["check_no_hardcoded"], "expected_output": "no_secrets", "description": "no hardcoded keys"},
            {"input": ["uses_env_var"], "expected_output": "env_var", "description": "uses env variables"},
            {"input": ["code_review"], "expected_output": "safe", "description": "passes review"},
        ],
    },
    {
        "id": "security_003",
        "domain": "web",
        "bug_description": "Unsafe eval of user input",
        "vulnerability_type": "unsafe_eval",
        "buggy_code": "def calculate(expression):\n    return eval(expression)",
        "fixed_code": "import ast\n\ndef calculate(expression):\n    try:\n        tree = ast.parse(expression, mode='eval')\n        for node in ast.walk(tree):\n            if not isinstance(node, (ast.Expression, ast.BinOp, ast.UnaryOp,\n                                     ast.Constant, ast.Add, ast.Sub,\n                                     ast.Mult, ast.Div, ast.USub)):\n                raise ValueError(f'Unsupported operation: {type(node).__name__}')\n        return eval(compile(tree, '<calc>', 'eval'))\n    except (SyntaxError, ValueError) as e:\n        raise ValueError(f'Invalid expression: {e}')",
        "hints": ["eval() can execute arbitrary code"],
        "security_concepts": ["code injection", "eval", "arbitrary code execution", "ast", "sandboxing", "input validation"],
        "test_cases": [
            {"input": ["2+2"], "expected_output": 4, "description": "basic math"},
            {"input": ["__import__('os')"], "expected_output": "blocked", "description": "code injection blocked"},
            {"input": ["10*5"], "expected_output": 50, "description": "multiplication"},
        ],
    },
    {
        "id": "security_004",
        "domain": "filesystem",
        "bug_description": "Path traversal in file reader",
        "vulnerability_type": "path_traversal",
        "buggy_code": "import os\n\ndef read_file(base_dir, filename):\n    filepath = os.path.join(base_dir, filename)\n    with open(filepath, 'r') as f:\n        return f.read()",
        "fixed_code": "import os\n\ndef read_file(base_dir, filename):\n    base_dir = os.path.realpath(base_dir)\n    filepath = os.path.realpath(os.path.join(base_dir, filename))\n    if not filepath.startswith(base_dir):\n        raise ValueError('Access denied: path traversal detected')\n    with open(filepath, 'r') as f:\n        return f.read()",
        "hints": ["What happens with '../../../etc/passwd'?"],
        "security_concepts": ["path traversal", "directory traversal", "realpath", "canonicalization", "file access control"],
        "test_cases": [
            {"input": ["/app/data", "file.txt"], "expected_output": "allowed", "description": "normal access"},
            {"input": ["/app/data", "../../etc/passwd"], "expected_output": "blocked", "description": "traversal blocked"},
            {"input": ["/app/data", "../secrets.txt"], "expected_output": "blocked", "description": "parent dir blocked"},
        ],
    },
    {
        "id": "security_005",
        "domain": "serialization",
        "bug_description": "Insecure pickle deserialization",
        "vulnerability_type": "insecure_deserialization",
        "buggy_code": "import pickle\n\ndef load_data(data_bytes):\n    return pickle.loads(data_bytes)",
        "fixed_code": "import json\n\ndef load_data(data_str):\n    return json.loads(data_str)",
        "hints": ["pickle can execute arbitrary code during deserialization"],
        "security_concepts": ["deserialization", "pickle", "remote code execution", "json", "safe serialization", "untrusted data"],
        "test_cases": [
            {"input": ["{\"key\": \"value\"}"], "expected_output": {"key": "value"}, "description": "json works"},
            {"input": ["[1,2,3]"], "expected_output": [1, 2, 3], "description": "list works"},
            {"input": ["no_pickle"], "expected_output": "safe", "description": "no pickle usage"},
        ],
    },
    {
        "id": "security_006",
        "domain": "web",
        "bug_description": "Command injection via os.system",
        "vulnerability_type": "command_injection",
        "buggy_code": "import os\n\ndef ping_host(hostname):\n    os.system(f'ping -c 1 {hostname}')\n    return True",
        "fixed_code": "import subprocess\nimport shlex\n\ndef ping_host(hostname):\n    if not hostname.replace('.', '').replace('-', '').isalnum():\n        raise ValueError('Invalid hostname')\n    result = subprocess.run(\n        ['ping', '-c', '1', hostname],\n        capture_output=True, text=True, timeout=5\n    )\n    return result.returncode == 0",
        "hints": ["os.system with user input allows command injection"],
        "security_concepts": ["command injection", "os.system", "subprocess", "shell injection", "input validation", "allowlist"],
        "test_cases": [
            {"input": ["example.com"], "expected_output": "safe", "description": "normal host"},
            {"input": ["; rm -rf /"], "expected_output": "blocked", "description": "injection blocked"},
            {"input": ["$(cat /etc/passwd)"], "expected_output": "blocked", "description": "subshell blocked"},
        ],
    },
    {
        "id": "security_007",
        "domain": "database",
        "bug_description": "SQL injection in login query",
        "vulnerability_type": "sql_injection",
        "buggy_code": "def login(db, user, password):\n    sql = \"SELECT * FROM users WHERE username='\" + user + \"' AND password='\" + password + \"'\"\n    result = db.execute(sql).fetchone()\n    return result is not None",
        "fixed_code": "def login(db, user, password):\n    sql = \"SELECT * FROM users WHERE username=? AND password=?\"\n    result = db.execute(sql, (user, password)).fetchone()\n    return result is not None",
        "hints": ["String concatenation in SQL queries"],
        "security_concepts": ["sql injection", "authentication bypass", "parameterized query", "prepared statement"],
        "test_cases": [
            {"input": ["admin", "pass"], "expected_output": "parameterized", "description": "uses params"},
            {"input": ["' OR 1=1--", "x"], "expected_output": "safe", "description": "injection safe"},
            {"input": ["user", "pass"], "expected_output": "parameterized", "description": "normal safe"},
        ],
    },
    {
        "id": "security_008",
        "domain": "api",
        "bug_description": "Hardcoded database password",
        "vulnerability_type": "hardcoded_secret",
        "buggy_code": "import psycopg2\n\ndef get_connection():\n    return psycopg2.connect(\n        host='db.example.com',\n        database='myapp',\n        user='admin',\n        password='super_secret_password_123'\n    )",
        "fixed_code": "import os\nimport psycopg2\n\ndef get_connection():\n    return psycopg2.connect(\n        host=os.environ['DB_HOST'],\n        database=os.environ['DB_NAME'],\n        user=os.environ['DB_USER'],\n        password=os.environ['DB_PASSWORD']\n    )",
        "hints": ["Database credentials in source code"],
        "security_concepts": ["hardcoded credentials", "database security", "environment variable", "configuration management", "secret rotation"],
        "test_cases": [
            {"input": ["check_no_hardcoded"], "expected_output": "no_secrets", "description": "no hardcoded creds"},
            {"input": ["uses_env_var"], "expected_output": "env_var", "description": "uses env variables"},
            {"input": ["code_review"], "expected_output": "safe", "description": "passes review"},
        ],
    },
    {
        "id": "security_009",
        "domain": "web",
        "bug_description": "Eval used for JSON parsing",
        "vulnerability_type": "unsafe_eval",
        "buggy_code": "def parse_config(config_str):\n    return eval(config_str)",
        "fixed_code": "import json\n\ndef parse_config(config_str):\n    return json.loads(config_str)",
        "hints": ["Don't use eval to parse data formats"],
        "security_concepts": ["code injection", "eval", "json.loads", "safe parsing", "data validation"],
        "test_cases": [
            {"input": ["{\"key\": 1}"], "expected_output": {"key": 1}, "description": "json works"},
            {"input": ["[1, 2]"], "expected_output": [1, 2], "description": "list works"},
            {"input": ["no_eval"], "expected_output": "safe", "description": "no eval usage"},
        ],
    },
    {
        "id": "security_010",
        "domain": "filesystem",
        "bug_description": "Arbitrary file write via path traversal",
        "vulnerability_type": "path_traversal",
        "buggy_code": "def save_upload(upload_dir, filename, content):\n    import os\n    path = os.path.join(upload_dir, filename)\n    with open(path, 'w') as f:\n        f.write(content)\n    return path",
        "fixed_code": "def save_upload(upload_dir, filename, content):\n    import os\n    upload_dir = os.path.realpath(upload_dir)\n    safe_name = os.path.basename(filename)\n    path = os.path.realpath(os.path.join(upload_dir, safe_name))\n    if not path.startswith(upload_dir):\n        raise ValueError('Invalid filename')\n    with open(path, 'w') as f:\n        f.write(content)\n    return path",
        "hints": ["Filename could contain ../ sequences"],
        "security_concepts": ["path traversal", "file upload", "basename", "directory confinement", "filename sanitization"],
        "test_cases": [
            {"input": ["/uploads", "file.txt", "data"], "expected_output": "allowed", "description": "normal upload"},
            {"input": ["/uploads", "../../etc/cron.d/evil", "data"], "expected_output": "blocked", "description": "traversal blocked"},
            {"input": ["/uploads", "../secret.txt", "data"], "expected_output": "blocked", "description": "parent blocked"},
        ],
    },
    {
        "id": "security_011",
        "domain": "serialization",
        "bug_description": "YAML unsafe load",
        "vulnerability_type": "insecure_deserialization",
        "buggy_code": "import yaml\n\ndef load_config(config_str):\n    return yaml.load(config_str)",
        "fixed_code": "import yaml\n\ndef load_config(config_str):\n    return yaml.safe_load(config_str)",
        "hints": ["yaml.load without Loader is unsafe"],
        "security_concepts": ["deserialization", "yaml", "safe_load", "arbitrary code execution", "configuration parsing"],
        "test_cases": [
            {"input": ["key: value"], "expected_output": {"key": "value"}, "description": "basic yaml"},
            {"input": ["list:\n  - 1\n  - 2"], "expected_output": {"list": [1, 2]}, "description": "yaml list"},
            {"input": ["safe_load_used"], "expected_output": "safe", "description": "uses safe_load"},
        ],
    },
    {
        "id": "security_012",
        "domain": "web",
        "bug_description": "Shell injection via subprocess shell=True",
        "vulnerability_type": "command_injection",
        "buggy_code": "import subprocess\n\ndef list_files(directory):\n    result = subprocess.run(\n        f'ls -la {directory}',\n        shell=True, capture_output=True, text=True\n    )\n    return result.stdout",
        "fixed_code": "import subprocess\nimport os\n\ndef list_files(directory):\n    directory = os.path.realpath(directory)\n    result = subprocess.run(\n        ['ls', '-la', directory],\n        capture_output=True, text=True\n    )\n    return result.stdout",
        "hints": ["shell=True with user input enables injection"],
        "security_concepts": ["command injection", "shell=True", "subprocess", "argument list", "input validation"],
        "test_cases": [
            {"input": ["/home/user"], "expected_output": "safe", "description": "normal dir"},
            {"input": ["; cat /etc/shadow"], "expected_output": "blocked", "description": "injection blocked"},
            {"input": ["$(whoami)"], "expected_output": "blocked", "description": "subshell blocked"},
        ],
    },
    {
        "id": "security_013",
        "domain": "database",
        "bug_description": "SQL injection in search endpoint",
        "vulnerability_type": "sql_injection",
        "buggy_code": "def search_products(db, query):\n    sql = f\"SELECT * FROM products WHERE name LIKE '%{query}%'\"\n    return db.execute(sql).fetchall()",
        "fixed_code": "def search_products(db, query):\n    sql = \"SELECT * FROM products WHERE name LIKE ?\"\n    return db.execute(sql, (f'%{query}%',)).fetchall()",
        "hints": ["LIKE clause is also vulnerable to injection"],
        "security_concepts": ["sql injection", "LIKE clause", "parameterized query", "search injection"],
        "test_cases": [
            {"input": ["laptop"], "expected_output": "parameterized", "description": "normal search"},
            {"input": ["'; DELETE FROM products;--"], "expected_output": "safe", "description": "injection safe"},
            {"input": ["test"], "expected_output": "parameterized", "description": "basic search"},
        ],
    },
    {
        "id": "security_014",
        "domain": "api",
        "bug_description": "JWT secret hardcoded",
        "vulnerability_type": "hardcoded_secret",
        "buggy_code": "import jwt\n\nSECRET = 'my-jwt-secret-key-12345'\n\ndef create_token(user_id):\n    return jwt.encode({'user_id': user_id}, SECRET, algorithm='HS256')\n\ndef verify_token(token):\n    return jwt.decode(token, SECRET, algorithms=['HS256'])",
        "fixed_code": "import os\nimport jwt\n\ndef create_token(user_id):\n    secret = os.environ['JWT_SECRET']\n    return jwt.encode({'user_id': user_id}, secret, algorithm='HS256')\n\ndef verify_token(token):\n    secret = os.environ['JWT_SECRET']\n    return jwt.decode(token, secret, algorithms=['HS256'])",
        "hints": ["JWT signing key should not be in source code"],
        "security_concepts": ["hardcoded secret", "JWT", "token signing", "environment variable", "key management"],
        "test_cases": [
            {"input": ["check_no_hardcoded"], "expected_output": "no_secrets", "description": "no hardcoded keys"},
            {"input": ["uses_env_var"], "expected_output": "env_var", "description": "uses env variables"},
            {"input": ["code_review"], "expected_output": "safe", "description": "passes review"},
        ],
    },
    {
        "id": "security_015",
        "domain": "web",
        "bug_description": "Exec used for template rendering",
        "vulnerability_type": "unsafe_eval",
        "buggy_code": "def render_template(template, context):\n    for key, value in context.items():\n        template = template.replace('{{' + key + '}}', str(value))\n    exec_code = f\"result = f'''{template}'''\"\n    local_vars = {}\n    exec(exec_code, {}, local_vars)\n    return local_vars['result']",
        "fixed_code": "def render_template(template, context):\n    result = template\n    for key, value in context.items():\n        result = result.replace('{{' + key + '}}', str(value))\n    return result",
        "hints": ["exec is as dangerous as eval"],
        "security_concepts": ["code injection", "exec", "template injection", "server-side template injection", "SSTI"],
        "test_cases": [
            {"input": ["Hello {{name}}", {"name": "World"}], "expected_output": "Hello World", "description": "basic render"},
            {"input": ["{{a}} + {{b}}", {"a": "1", "b": "2"}], "expected_output": "1 + 2", "description": "multi var"},
            {"input": ["no exec"], "expected_output": "safe", "description": "no exec usage"},
        ],
    },
    {
        "id": "security_016",
        "domain": "filesystem",
        "bug_description": "Symlink attack in temp file handling",
        "vulnerability_type": "path_traversal",
        "buggy_code": "import os\n\ndef write_temp(name, data):\n    path = f'/tmp/{name}'\n    with open(path, 'w') as f:\n        f.write(data)\n    return path",
        "fixed_code": "import tempfile\nimport os\n\ndef write_temp(name, data):\n    safe_name = os.path.basename(name)\n    fd, path = tempfile.mkstemp(prefix=safe_name + '_', dir='/tmp')\n    with os.fdopen(fd, 'w') as f:\n        f.write(data)\n    return path",
        "hints": ["Predictable temp file paths enable symlink attacks"],
        "security_concepts": ["symlink attack", "temporary file", "race condition", "mkstemp", "secure temp files"],
        "test_cases": [
            {"input": ["data.txt", "content"], "expected_output": "safe_temp", "description": "safe temp creation"},
            {"input": ["../../etc/passwd", "evil"], "expected_output": "blocked", "description": "traversal blocked"},
            {"input": ["normal.log", "log data"], "expected_output": "safe_temp", "description": "normal temp"},
        ],
    },
]


def _build_entries(raw: list[dict], bug_type: BugType, difficulty: Difficulty) -> list[BugEntry]:
    entries: list[BugEntry] = []
    for item in raw:
        test_cases = [TestCase(**tc) for tc in item.get("test_cases", [])]
        vuln = None
        if item.get("vulnerability_type"):
            vuln = VulnerabilityType(item["vulnerability_type"])
        entries.append(BugEntry(
            id=item["id"],
            buggy_code=item["buggy_code"],
            fixed_code=item["fixed_code"],
            bug_type=bug_type,
            difficulty=difficulty,
            domain=item.get("domain", "general"),
            bug_description=item.get("bug_description", ""),
            vulnerability_type=vuln,
            test_cases=test_cases,
            error_message=item.get("error_message", ""),
            hints=item.get("hints", []),
            security_concepts=item.get("security_concepts", []),
        ))
    return entries


_CORPUS: list[BugEntry] | None = None


def get_corpus() -> list[BugEntry]:
    """Return the full 52-entry bug corpus (cached)."""
    global _CORPUS
    if _CORPUS is None:
        _CORPUS = (
            _build_entries(_SYNTAX_BUGS, BugType.SYNTAX, Difficulty.EASY)
            + _build_entries(_LOGIC_BUGS, BugType.LOGIC, Difficulty.MEDIUM)
            + _build_entries(_SECURITY_BUGS, BugType.SECURITY, Difficulty.HARD)
        )
    return _CORPUS


def get_bugs_by_type(bug_type: BugType) -> list[BugEntry]:
    """Filter corpus by bug type."""
    return [b for b in get_corpus() if b.bug_type == bug_type]


def get_bug_by_id(bug_id: str) -> BugEntry | None:
    """Lookup a single entry by ID."""
    for b in get_corpus():
        if b.id == bug_id:
            return b
    return None
