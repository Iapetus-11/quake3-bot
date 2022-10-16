from tortoise import fields

from .base_timestamped_model import BaseTimestampedModel


class BaseModel(BaseTimestampedModel):
    id = fields.IntField(pk=True)

    class Meta:
        abstract = True
