import re


def snake_to_pascal_case(snake_str: str) -> str:
    """Convert a snake_case string to PascalCase."""
    components = snake_str.strip("_").split("_")
    return "".join(x.title() for x in components)


def pascal_to_snake_case(pascal_str: str) -> str:
    """Convert a PascalCase string to snake_case with a leading underscore."""
    if not pascal_str:
        return ""

    # Insert underscores before each uppercase letter (except the first one)
    snake_str = re.sub(r"(?<!^)(?=[A-Z])", "_", pascal_str).lower()

    # Ensure there is a leading underscore
    if not snake_str.startswith("_"):
        snake_str = "_" + snake_str

    return snake_str


def snake_to_sentence_case(snake_str: str) -> str:
    # Remove leading underscores
    cleaned_str = snake_str.lstrip("_")
    # Replace underscores with spaces and capitalize the first letter of each word

    return " ".join(cleaned_str.split("_")).capitalize()


def camel_to_sentence_case(camel_str: str) -> str:
    # Insert spaces before capital letters and capitalize the first letter
    sentence_case_str = re.sub(r"([a-z])([A-Z])", r"\1 \2", camel_str).title()
    return sentence_case_str
