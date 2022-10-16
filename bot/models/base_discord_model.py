from tortoise import fields

from .base_timestamped_model import BaseTimestampedModel


class BaseDiscordModel(BaseTimestampedModel):
    id = fields.BigIntField(pk=True, generated=False)

    class Meta:
        abstract = True
