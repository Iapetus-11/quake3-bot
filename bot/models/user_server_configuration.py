from __future__ import annotations

import typing as t

from cryptography.fernet import Fernet
from tortoise import BaseDBAsyncClient, fields

from .base_model import BaseModel


class UserQuake3ServerConfiguration(BaseModel):
    server = fields.ForeignKeyField("models.Quake3Server", related_name="configurations")
    discord_user = fields.ForeignKeyField("models.DiscordUser", related_name="configurations")

    encrypted_password = fields.CharField(max_length=128)

    @property
    def password(self) -> str:
        from bot.config import CONFIG

        return (
            Fernet(CONFIG.RCON_PASSWORD_FERNET_KEY)
            .decrypt(self.encrypted_password.encode())
            .decode()
        )

    @classmethod
    async def create(
        cls, using_db: BaseDBAsyncClient | None = None, **kwargs: t.Any
    ) -> UserQuake3ServerConfiguration:
        from bot.config import CONFIG

        kwargs["encrypted_password"] = (
            Fernet(CONFIG.RCON_PASSWORD_FERNET_KEY)
            .encrypt(kwargs.pop("password").encode())
            .decode()
        )
        return await super(UserQuake3ServerConfiguration, cls).create(using_db=using_db, **kwargs)
