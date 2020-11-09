import uuid

from django.db import models

from api.common.models import TimestampableModel
from api.documents.models import Document
from api.flags.models import Flag
from api.goods.enums import (
    GoodStatus,
    PvGrading,
    GoodPvGraded,
    ItemCategory,
    MilitaryUse,
    Component,
    FirearmGoodType,
)

from api.organisations.models import Organisation
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.missing_document_reasons.enums import GoodMissingDocumentReasons
from api.users.models import ExporterUser


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


class FirearmGoodDetails(models.Model):
    type = models.CharField(choices=FirearmGoodType.choices, max_length=25, blank=False)
    year_of_manufacture = models.PositiveSmallIntegerField()
    calibre = models.TextField(blank=False, max_length=15)
    # this refers specifically to section 1, 2 or 5 of firearms act 1968
    is_covered_by_firearm_act_section_one_two_or_five = models.BooleanField()
    section_certificate_number = models.CharField(blank=True, max_length=100, null=True)
    section_certificate_date_of_expiry = models.DateField(blank=True, null=True)
    has_identification_markings = models.BooleanField(null=False)
    identification_markings_details = models.TextField(blank=True, max_length=2000, null=True)
    no_identification_markings_details = models.TextField(blank=True, max_length=2000, null=True)
    serial_number = models.TextField(default='')


class Good(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(max_length=280)

    # CLC. used as base values that can be overridden at application level
    is_good_controlled = models.BooleanField(default=None, blank=True, null=True)
    control_list_entries = models.ManyToManyField(ControlListEntry, related_name="goods")

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
    item_category = models.CharField(choices=ItemCategory.choices, null=True, max_length=20)
    is_military_use = models.CharField(choices=MilitaryUse.choices, null=True, max_length=15)
    modified_military_use_details = models.TextField(default=None, blank=True, null=True, max_length=2000)
    is_component = models.CharField(choices=Component.choices, null=True, max_length=15)
    component_details = models.TextField(default=None, blank=True, null=True, max_length=2000)
    uses_information_security = models.BooleanField(default=None, null=True)
    information_security_details = models.TextField(default=None, blank=True, null=True, max_length=2000)
    firearm_details = models.ForeignKey(
        FirearmGoodDetails, on_delete=models.CASCADE, default=None, blank=True, null=True
    )
    software_or_technology_details = models.TextField(default=None, blank=True, null=True, max_length=2000)

    # Gov
    # comment responding to CLC query
    comment = models.TextField(default=None, blank=True, null=True, max_length=2000)
    # comment about the PV grading response set by gov user
    grading_comment = models.TextField(default=None, blank=True, null=True, max_length=2000)
    # max length same as picklist
    report_summary = models.TextField(default=None, blank=True, null=True, max_length=5000)

    class Meta:
        db_table = "good"
        ordering = ["-created_at"]


class GoodDocument(Document):
    good = models.ForeignKey(Good, on_delete=models.CASCADE)
    user = models.ForeignKey(ExporterUser, on_delete=models.DO_NOTHING)
    organisation = models.ForeignKey(Organisation, on_delete=models.DO_NOTHING)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
