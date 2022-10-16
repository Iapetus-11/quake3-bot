from tortoise.models import Model
from tortoise import fields


class BaseTimestampedModel(Model):
    updated_at = fields.DatetimeField(auto_now=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True
