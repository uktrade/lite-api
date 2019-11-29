from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.fields import AutoCreatedField, AutoLastModifiedField


class CreatedAt(models.Model):
    created_at = AutoCreatedField(_("created_at"))

    class Meta:
        abstract = True


class TimestampableModel(CreatedAt):
    updated_at = AutoLastModifiedField(_("updated_at"))

    class Meta:
        abstract = True
