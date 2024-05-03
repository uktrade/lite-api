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
        ReportSummaryPrefix, blank=True, null=True, related_name="prefix", on_delete=models.DO_NOTHING
    )
    subject = models.ForeignKey(
        ReportSummarySubject, blank=True, null=True, related_name="subject", on_delete=models.DO_NOTHING
    )

    def __repr__(self):
        report_summary = self.subject.name
        if self.prefix:
            report_summary = f"{self.prefix.name} {self.subject.name}"

        return report_summary
