import uuid

from django.db import models

from cases.models import CaseType, Case
from api.common.models import TimestampableModel
from open_general_licences.enums import OpenGeneralLicenceStatus
from api.organisations.models import Site
from static.control_list_entries.models import ControlListEntry
from static.countries.models import Country


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


class OpenGeneralLicenceCase(Case):
    open_general_licence = models.ForeignKey(
        OpenGeneralLicence, related_name="cases", blank=False, null=False, on_delete=models.CASCADE
    )
    site = models.ForeignKey(
        Site, related_name="open_general_licence_cases", blank=False, null=False, on_delete=models.CASCADE
    )

    class Meta:
        db_table = "open_general_licence_case"

    def save(self, *args, **kwargs):
        from open_general_licences.helpers import issue_open_general_licence

        creating = self._state.adding
        super(OpenGeneralLicenceCase, self).save(*args, **kwargs)

        if creating:
            issue_open_general_licence(self)
