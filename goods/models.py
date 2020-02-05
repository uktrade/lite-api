import uuid

from django.db import models

from common.models import TimestampableModel
from documents.models import Document
from flags.models import Flag
from goods.enums import GoodStatus, GoodControlled, PvGrading, GoodPvGraded
from organisations.models import Organisation
from static.missing_document_reasons.enums import GoodMissingDocumentReasons
from users.models import ExporterUser


class PvGradingDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # grading is required if custom_grading is not provided
    grading = models.CharField(choices=PvGrading.choices, default=None, blank=True, null=True, max_length=30)
    # custom_grading is required if grading is not provided
    custom_grading = models.TextField(blank=True, null=True, max_length=100)
    prefix = models.CharField(blank=True, null=True, max_length=30)
    suffix = models.CharField(blank=True, null=True, max_length=30)
    issuing_authority = models.CharField(blank=True, null=True, max_length=100)
    reference = models.CharField(blank=True, null=True, max_length=100)
    date_of_issue = models.DateField(blank=True, null=True)


class Good(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(max_length=280)

    # CLC
    is_good_controlled = models.CharField(choices=GoodControlled.choices, default=GoodControlled.UNSURE, max_length=20)
    control_code = models.CharField(default="", blank=True, null=True, max_length=20)

    # PV
    is_pv_graded = models.CharField(choices=GoodPvGraded.choices, default=GoodPvGraded.GRADING_REQUIRED, max_length=20)
    pv_grading_details = models.ForeignKey(
        PvGradingDetails, on_delete=models.CASCADE, default=None, blank=True, null=True
    )

    part_number = models.CharField(default="", blank=True, null=True, max_length=255)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    status = models.CharField(choices=GoodStatus.choices, default=GoodStatus.DRAFT, max_length=20)
    flags = models.ManyToManyField(Flag, related_name="goods")
    missing_document_reason = models.CharField(choices=GoodMissingDocumentReasons.choices, null=True, max_length=30)

    # Gov
    # comment about reviewing good, or responding to CLC query
    comment = models.TextField(default=None, blank=True, null=True, max_length=2000)
    # comment about the PV grading response set by gov user
    grading_comment = models.TextField(default=None, blank=True, null=True, max_length=2000)
    # max length same as picklist
    report_summary = models.TextField(default=None, blank=True, null=True, max_length=5000)


class GoodDocument(Document):
    good = models.ForeignKey(Good, on_delete=models.CASCADE)
    user = models.ForeignKey(ExporterUser, on_delete=models.DO_NOTHING)
    organisation = models.ForeignKey(Organisation, on_delete=models.DO_NOTHING)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
