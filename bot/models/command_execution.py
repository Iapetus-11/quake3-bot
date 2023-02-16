from tortoise import fields

from bot.models import BaseModel


class CommandExecution(BaseModel):
    name = fields.CharField(max_length=32)

    discord_user = fields.ForeignKeyField("models.DiscordUser", related_name="command_executions")
    discord_guild = fields.ForeignKeyField("models.DiscordGuild", related_name="command_executions")

    discord_channel_id = fields.BigIntField()
