"""
Colours for terminal output
Example usage: colours.green('Days of Brutalism')
"""

GREEN = "\033[92m"
ORANGE = "\033[93m"
RED = "\033[91m"
END = "\033[0m"


def green(text):
    return f"{GREEN}{text}{END}"


def orange(text):
    return f"{ORANGE}{text}{END}"


def red(text):
    return f"{RED}{text}{END}"
