def truncate_string(string: str, to: int, *, ellipses: str = "…") -> str:
    if len(string) > to:
        return string[: to - len(ellipses)] + ellipses

    return string
