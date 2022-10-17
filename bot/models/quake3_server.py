from tortoise import fields

from .user_server_configuration import UserQuake3ServerConfiguration
from .base_model import BaseModel


class Quake3Server(BaseModel):
    address = fields.CharField(max_length=128)

    discord_guild = fields.ForeignKeyField(
        "models.DiscordGuild", related_name="quake3_servers", null=True
    )

    configurations: fields.ReverseRelation["UserQuake3ServerConfiguration"]

    @property
    def host(self) -> str:
        return self.address.split(':')[0]

    @property
    def port(self) -> int:
        if ":" in self.address:
            return int(self.address.split(":")[-1])

        return 27960
