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


class ReportSummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prefix = models.ForeignKey(
        ReportSummaryPrefix, blank=True, null=True, related_name="prefix", on_delete=models.PROTECT
    )
    subject = models.ForeignKey(ReportSummarySubject, related_name="subject", on_delete=models.PROTECT)

    class Meta:
        unique_together = [["prefix", "subject"]]

    @property
    def name(self):
        if self.prefix:
            return f"{self.prefix.name} {self.subject.name}"

        return self.subject.name

    def __repr__(self):
        return self.name
