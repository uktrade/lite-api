import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models

from api.common.models import TimestampableModel
from api.exporter_answers.enums import STATUS_CHOICES, STATUS_DRAFT, STATUS_SUBMITTED, STATUS_SUPERSEDED
from api.users.models import ExporterUser


class ExporterAnswerSet(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flow = models.CharField(max_length=2000)
    section = models.CharField(max_length=2000)
    answers = models.JSONField()
    questions = models.JSONField()
    answer_fields = ArrayField(models.CharField(max_length=200))
    frontend_commit_sha = models.CharField(max_length=40)
    status = models.CharField(choices=STATUS_CHOICES, default=STATUS_DRAFT, max_length=50)
    created_by = models.ForeignKey(ExporterUser, on_delete=models.DO_NOTHING, related_name="exporter_answer_sets")
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_object_id = models.UUIDField()
    target_object = GenericForeignKey("target_content_type", "target_object_id")
    superseded_by = models.ForeignKey("exporter_answers.ExporterAnswerSet", on_delete=models.CASCADE, null=True)

    def supersede_existing(self):
        existing_answer_sets = ExporterAnswerSet.objects.filter(
            flow=self.flow,
            section=self.section,
            status__in=[STATUS_DRAFT, STATUS_SUBMITTED],
            superseded_by__isnull=True,
        ).exclude(id=self.id)
        existing_answer_sets.update(status=STATUS_SUPERSEDED, superseded_by=self)

    def save(self, **kwargs):
        if self.answers:
            self.answer_fields = list(self.answers.keys())
        super().save(**kwargs)
        self.supersede_existing()
