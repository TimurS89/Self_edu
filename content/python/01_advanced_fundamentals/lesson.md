# Advanced Python Fundamentals: Decorators

## What Are Decorators?

Decorators are a powerful Python feature that lets you modify or extend the behavior of functions without changing their code. A decorator is simply a function that takes another function as an argument and returns a new function.

## Basic Decorator Pattern

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before the function call")
        result = func(*args, **kwargs)
        print("After the function call")
        return result
    return wrapper

@my_decorator
def say_hello(name):
    print(f"Hello, {name}!")

say_hello("World")
# Output:
# Before the function call
# Hello, World!
# After the function call
```

The `@my_decorator` syntax is equivalent to writing `say_hello = my_decorator(say_hello)`.

## Why Decorators Matter

Decorators are used everywhere in Python:
- **Flask**: `@app.route("/")` maps URLs to functions
- **pytest**: `@pytest.fixture` defines test fixtures
- **functools**: `@lru_cache` adds caching to any function
- **dataclasses**: `@dataclass` generates boilerplate for data classes

## Decorator with Arguments

To create a decorator that accepts arguments, you need an extra layer of nesting:

```python
def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def greet():
    print("Hello!")

greet()  # Prints "Hello!" three times
```

## Preserving Function Metadata

Always use `functools.wraps` to preserve the original function's name and docstring:

```python
from functools import wraps

def my_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

Without `@wraps`, `func.__name__` and `func.__doc__` would show the wrapper's info instead of the original function's.

## Key Takeaways

1. Decorators wrap functions to add behavior
2. Use `@wraps` from `functools` to preserve metadata
3. Decorators with arguments need three levels of nesting
4. They're central to Flask, pytest, and many Python libraries you'll use for AI/ML
