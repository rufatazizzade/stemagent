# Safe example: No vulnerabilities present
# This file serves as a negative control in the security benchmark.

from typing import List


def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def greet(name: str) -> str:
    """Return a greeting string."""
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    return f"Hello, {name}!"


def fibonacci(n: int) -> List[int]:
    """Generate the first n Fibonacci numbers."""
    if n <= 0:
        return []
    if n == 1:
        return [0]
    sequence = [0, 1]
    for _ in range(2, n):
        sequence.append(sequence[-1] + sequence[-2])
    return sequence


def is_palindrome(text: str) -> bool:
    """Check if a string is a palindrome."""
    cleaned = text.lower().replace(" ", "")
    return cleaned == cleaned[::-1]


if __name__ == "__main__":
    print(add(2, 3))
    print(greet("World"))
    print(fibonacci(10))
    print(is_palindrome("racecar"))
