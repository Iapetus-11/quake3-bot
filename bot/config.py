from typing import Any, Dict

import dotenv
from pydantic import BaseModel, Field


class BotConfig(BaseModel):
    DISCORD_BOT_TOKEN: str

    DATABASE_NAME: str = Field(default="bot.db")

    COMMAND_PREFIX: str = Field(default="!")


def load_config() -> BotConfig:
    return BotConfig(**dotenv.dotenv_values())


def _get_field_value_or_example(field_data: Dict[str, Any]) -> object:
    if "default" in field_data:
        return str(field_data["default"])

    data_type = field_data.get("type")

    if data_type == "integer":
        return 123456

    if data_type == "number":
        return 123.456

    return data_type


def generate_example_env():
    lines = []
    current_section = ""

    for name, field_data in BotConfig.schema()["properties"].items():
        name: str
        field_data: dict

        if (section := name.split("_")[0]) != current_section:
            current_section = section
            lines.append("\n")

        lines.append(f"{name}={_get_field_value_or_example(field_data)}\n")

    with open("example.env", "w+") as example_env:
        example_env.writelines(lines[1:])


if __name__ == "__main__":
    print("Generating example.env file...")
    generate_example_env()
    print("Done!")
