from tortoise import fields

from .base_discord_model import BaseDiscordModel
from .quake3_server import Quake3Server


class DiscordGuild(BaseDiscordModel):
    quake3_servers: fields.ReverseRelation["Quake3Server"]
