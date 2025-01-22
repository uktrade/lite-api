import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models

from api.common.models import TimestampableModel
from api.exporter_answers.enums import STATUS_CHOICES, STATUS_DRAFT
from api.users.models import ExporterUser


class ExporterAnswerSet(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flow = models.CharField(max_length=2000)
    section = models.CharField(max_length=2000)
    answers = models.JSONField()
    answer_fields = ArrayField(models.CharField(max_length=200))
    frontend_commit_sha = models.CharField(max_length=40)
    status = models.CharField(choices=STATUS_CHOICES, default=STATUS_DRAFT, max_length=50)
    created_by = models.ForeignKey(ExporterUser, on_delete=models.DO_NOTHING, related_name="exporter_answer_sets")
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_object_id = models.UUIDField()
    target_object = GenericForeignKey("target_content_type", "target_object_id")

    def save(self, **kwargs):
        if self.answers:
            self.answer_fields = list(self.answers.keys())
        return super().save(**kwargs)
