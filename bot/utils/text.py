import io

import discord

VALID_Q3_IDENT_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789-_."


def truncate_string(string: str, to: int, *, ellipses: str = "…") -> str:
    if len(string) > to:
        return string[: to - len(ellipses)] + ellipses

    return string


def validate_q3_identifier(string: str) -> bool:
    return len(string.lower().strip(VALID_Q3_IDENT_CHARS)) == 0


def text_to_discord_file(text: str, *, file_name: str | None = None) -> discord.File:
    file_data = io.BytesIO(text.encode(encoding="utf8"))
    file_data.seek(0)
    return discord.File(file_data, filename=file_name)
