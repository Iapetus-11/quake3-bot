from tortoise import fields

from .quake3_server import Quake3Server
from .base_discord_model import BaseDiscordModel


class DiscordGuild(BaseDiscordModel):
    quake3_servers: fields.ReverseRelation["Quake3Server"]
