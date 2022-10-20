VALID_Q3_IDENT_CHARS = "abcdefghijklnopqrstuvwxyz0123456789-_"

def truncate_string(string: str, to: int, *, ellipses: str = "…") -> str:
    if len(string) > to:
        return string[: to - len(ellipses)] + ellipses

    return string


def validate_q3_identifier(string: str) -> bool:
    return len(string.strip(VALID_Q3_IDENT_CHARS)) == 0
