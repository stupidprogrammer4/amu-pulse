_VOWELS = ("a", "e", "i", "o", "u")


def pluralize(word: str) -> str:
    result = word + "s"
    if not word:
        result = word
    elif word.endswith(("s", "x", "z", "ch", "sh")):
        result = word + "es"
    elif word.endswith("y") and word[-2:-1] not in _VOWELS:
        result = word[:-1] + "ies"
    return result
