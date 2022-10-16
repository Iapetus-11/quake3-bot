from tortoise import fields

from .base_model import BaseModel


class Quake3Server(BaseModel):
    address = fields.CharField(max_length=128)

    discord_guild_id = fields.ForeignKeyField(
        "models.DiscordGuild", related_name="quake3_servers", null=True
    )
