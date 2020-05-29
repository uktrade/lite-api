from django.db import models

from common.models import TimestampableModel
from gov_notify.enums import TemplateType


class GovNotifyTemplate(TimestampableModel):
    template_type = models.CharField(choices=[(tag, tag.value) for tag in TemplateType], max_length=255, db_index=True)
    template_id = models.UUIDField()
