I have a Python module for a simple calculator. Here is the code:

# calculator.py

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b != 0:
        return a / b
    else:
        return "Cannot divide by zero"

I want to rename the variable `a` to `x` in all functions. Please provide a diff for the changes.
