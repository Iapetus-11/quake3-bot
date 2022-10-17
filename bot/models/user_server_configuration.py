from .base_model import BaseModel

from tortoise import fields


class UserQuake3ServerConfiguration(BaseModel):
    server = fields.ForeignKeyField('models.Quake3Server', related_name="configurations")
    discord_user = fields.ForeignKeyField('models.DiscordUser', related_name="configurations")

    password = fields.CharField(max_length=128)
