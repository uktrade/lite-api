import uuid

from django.db import models


class ReportSummaryPrefix(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    def __repr__(self):
        return self.name


class ReportSummarySubject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    code_level = models.IntegerField()

    def __repr__(self):
        return self.name
