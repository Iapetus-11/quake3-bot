from tortoise import fields
from tortoise.models import Model


class BaseTimestampedModel(Model):
    updated_at = fields.DatetimeField(auto_now=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True
