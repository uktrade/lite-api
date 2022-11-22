import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models

from api.common.models import TimestampableModel
from api.documents.models import Document
from api.flags.models import Flag
from api.goods.enums import (
    Component,
    FirearmCategory,
    FirearmGoodType,
    GoodPvGraded,
    GoodStatus,
    ItemCategory,
    MilitaryUse,
    PvGrading,
)

from api.organisations.models import Organisation
from api.staticdata.control_list_entries.models import ControlListEntry
from api.users.models import ExporterUser


class PvGradingDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # grading is required if custom_grading is not provided
    grading = models.CharField(
        choices=PvGrading.choices + PvGrading.choices_new, default=None, blank=True, null=True, max_length=30
    )
    # custom_grading is required if grading is not provided
    custom_grading = models.TextField(blank=True, null=True, max_length=100)
    prefix = models.CharField(blank=True, null=True, max_length=30)
    suffix = models.CharField(blank=True, null=True, max_length=30)
    issuing_authority = models.TextField(default="")
    reference = models.CharField(blank=True, null=True, max_length=100)
    date_of_issue = models.DateField(blank=True, null=True)


class FirearmGoodDetails(models.Model):
    class SerialNumberAvailability(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Yes, I can add serial numbers now"
        LATER = "LATER", "Yes, I can add serial numbers later"
        NOT_AVAILABLE = "NOT_AVAILABLE", "No"

        @classmethod
        def get_has_serial_numbers_values(cls):
            return [cls.AVAILABLE, cls.LATER]

        @classmethod
        def has_serial_numbers(cls, value):
            return value in cls.get_has_serial_numbers_values()

    type = models.TextField(choices=FirearmGoodType.choices, blank=False)
    category = ArrayField(models.CharField(choices=FirearmCategory.choices, max_length=255), blank=True, null=True)
    is_made_before_1938 = models.BooleanField(blank=True, null=True)
    year_of_manufacture = models.PositiveSmallIntegerField(blank=True, null=True)
    calibre = models.TextField(blank=True)
    is_replica = models.BooleanField(blank=True, null=True)
    replica_description = models.TextField(blank=True, default="")
    # this refers specifically to section 1, 2 or 5 of firearms act 1968
    is_covered_by_firearm_act_section_one_two_or_five = models.TextField(blank=True, default="")
    is_covered_by_firearm_act_section_one_two_or_five_explanation = models.TextField(blank=True, default="")
    firearms_act_section = models.TextField(blank=True, default="")

    section_certificate_missing = models.BooleanField(blank=True, null=True)
    section_certificate_missing_reason = models.TextField(blank=True, default="")
    section_certificate_number = models.CharField(blank=True, max_length=100, null=True)
    section_certificate_date_of_expiry = models.DateField(blank=True, null=True)

    no_identification_markings_details = models.TextField(blank=True, max_length=2000, null=True)
    serial_numbers_available = models.CharField(
        blank=True,
        choices=SerialNumberAvailability.choices,
        max_length=255,
        null=True,
    )
    serial_number = models.TextField(default="")
    number_of_items = models.PositiveIntegerField(blank=True, null=True)
    serial_numbers = ArrayField(models.TextField(default=""), default=list)
    has_proof_mark = models.BooleanField(
        help_text="Has been proofed (by a proof house) indicating it is safe to be used.", null=True
    )
    no_proof_mark_details = models.TextField(
        help_text="The reason why `has_proof_mark` is False (which should normally be True).", blank=True, default=""
    )
    is_deactivated = models.BooleanField(help_text="Has the firearms been deactivated?", null=True)
    is_deactivated_to_standard = models.BooleanField(
        help_text="Has the firearms been deactivated to UK/EU standards?", null=True
    )
    date_of_deactivation = models.DateField(blank=True, null=True)
    not_deactivated_to_standard_comments = models.TextField(default="")
    deactivation_standard = models.TextField(default="")
    deactivation_standard_other = models.TextField(default="")

    # Onward export
    is_onward_exported = models.BooleanField(default=None, blank=True, null=True)
    is_onward_altered_processed = models.BooleanField(default=None, blank=True, null=True)
    is_onward_altered_processed_comments = models.TextField(
        default="", blank=True, null=True, help_text="How the product will be processed or altered"
    )
    is_onward_incorporated = models.BooleanField(default=None, blank=True, null=True)
    is_onward_incorporated_comments = models.TextField(
        default="", blank=True, null=True, help_text="what's being incorporated into the product"
    )

    @property
    def has_serial_numbers(self):
        return self.SerialNumberAvailability.has_serial_numbers(self.serial_numbers_available)


class GoodControlListEntry(models.Model):
    good = models.ForeignKey("Good", related_name="goods", on_delete=models.CASCADE)
    controllistentry = models.ForeignKey(ControlListEntry, related_name="controllistentries", on_delete=models.CASCADE)

    class Meta:
        """
        This table name should not be modified, this is the through table name that Django created for us
        when previously 'through' table was not specified for the M2M field 'control_list_entries' in
        'Good' model below. We have recently updated the field to use this model as the through table
        and we don't want Django to create a new table but use the previously inferred through table
        instead hence we are specifying the same table name using the 'db_table' attribute.
        """

        db_table = "good_control_list_entries"


class Good(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField()

    # CLC. used as base values that can be overridden at application level
    is_good_controlled = models.BooleanField(default=None, blank=True, null=True)
    control_list_entries = models.ManyToManyField(ControlListEntry, related_name="goods", through=GoodControlListEntry)

    # PV
    is_pv_graded = models.CharField(choices=GoodPvGraded.choices, default=GoodPvGraded.GRADING_REQUIRED, max_length=20)
    pv_grading_details = models.ForeignKey(
        PvGradingDetails, on_delete=models.SET_NULL, default=None, blank=True, null=True
    )

    part_number = models.CharField(default="", blank=True, null=True, max_length=255)
    no_part_number_comments = models.TextField(
        default="", blank=True, null=False, help_text="Comments from applicant reasoning why part number is included"
    )
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    status = models.CharField(choices=GoodStatus.choices, default=GoodStatus.DRAFT, max_length=20)
    flags = models.ManyToManyField(Flag, related_name="goods")
    is_document_available = models.BooleanField(default=None, null=True)
    is_document_sensitive = models.BooleanField(default=None, null=True)
    no_document_comments = models.TextField(
        default="", blank=True, null=False, help_text="Comments from applicant reasoning why no document is uploaded"
    )
    product_description = models.TextField(default="", blank=True, null=True)
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
    has_security_features = models.BooleanField(default=None, blank=True, null=True)
    security_feature_details = models.TextField(
        default="", blank=True, null=True, help_text="what security features incorporated into the product"
    )
    has_declared_at_customs = models.BooleanField(default=None, blank=True, null=True)
    design_details = models.TextField(default="", blank=True, null=True, help_text="what design details provided")

    class Meta:
        db_table = "good"
        ordering = ["-created_at"]

    def get_precedents(self):
        if self.status != GoodStatus.VERIFIED:
            return self.goods_on_application.none()

        return self.goods_on_application.filter(
            control_list_entries__isnull=False,
        )


class GoodDocument(Document):
    good = models.ForeignKey(Good, on_delete=models.CASCADE)
    user = models.ForeignKey(ExporterUser, on_delete=models.DO_NOTHING)
    organisation = models.ForeignKey(Organisation, on_delete=models.DO_NOTHING)
    description = models.TextField(default=None, blank=True, null=True)
