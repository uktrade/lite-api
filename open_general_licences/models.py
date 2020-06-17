import uuid

from django.db import models
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from cases.models import CaseType, Case
from common.models import TimestampableModel
from open_general_licences.enums import OpenGeneralLicenceStatus
from organisations.models import Site
from static.control_list_entries.models import ControlListEntry
from static.countries.models import Country
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class OpenGeneralLicence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(unique=True, max_length=250)
    description = models.TextField()
    url = models.URLField(blank=False, null=False)
    case_type = models.ForeignKey(
        CaseType, on_delete=models.DO_NOTHING, null=False, blank=False, related_name="OpenGeneralLicence"
    )
    countries = models.ManyToManyField(Country, related_name="OpenGeneralLicence")
    control_list_entries = models.ManyToManyField(ControlListEntry, related_name="OpenGeneralLicence")
    registration_required = models.BooleanField()
    status = models.CharField(
        choices=OpenGeneralLicenceStatus.choices,
        null=False,
        blank=False,
        default=OpenGeneralLicenceStatus.ACTIVE,
        max_length=20,
    )

    class Meta:
        db_table = "open_general_licence"
        ordering = ["name"]
        indexes = [models.Index(fields=["status", "name"])]

    def register_for_organisation(self, user, organisation):
        if self.status == OpenGeneralLicenceStatus.DEACTIVATED:
            raise ValidationError(
                {"open_general_licence": ["This open general licence is deactivated and cannot be registered"]}
            )

        if not self.registration_required:
            raise ValidationError({"open_general_licence": ["This open general licence does not require registration"]})

        # Only register open general licences for sites in the UK which don't already have that licence registered
        OpenGeneralLicenceCase.objects.bulk_create(
            [
                OpenGeneralLicenceCase(
                    open_general_licence=self,
                    site=site,
                    case_type=self.case_type,
                    organisation=organisation,
                    status=get_case_status_by_status(CaseStatusEnum.FINALISED),
                    submitted_at=timezone.now(),
                    submitted_by=user,
                ),
            ]
            for site in Site.objects.get_by_user_and_organisation(user, organisation).filter(address__country_id="GB")
            if not OpenGeneralLicenceCase.objects.filter(open_general_licence=self, site=site).exists()
        )

        return self.id


class OpenGeneralLicenceCase(Case):
    open_general_licence = models.ForeignKey(
        OpenGeneralLicence, related_name="cases", blank=False, null=False, on_delete=models.CASCADE
    )
    site = models.ForeignKey(
        Site, related_name="open_general_licence_cases", blank=False, null=False, on_delete=models.CASCADE
    )

    class Meta:
        db_table = "open_general_licence_case"
