from tortoise import fields

from .base_model import BaseModel


class UserQuake3ServerConfiguration(BaseModel):
    server = fields.ForeignKeyField("models.Quake3Server")
    discord_user = fields.ForeignKeyField("models.DiscordUser")

    password = fields.CharField(max_length=128)
