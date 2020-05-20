import uuid

from django.db import models

from cases.models import CaseType
from common.models import TimestampableModel
from open_general_licences.enums import OpenGeneralLicenceStatus
from static.control_list_entries.models import ControlListEntry
from static.countries.models import Country


class OpenGeneralLicence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(unique=True, max_length=250)
    description = models.TextField()
    url = models.URLField(default=None, blank=False, null=False)
    case_type = models.ForeignKey(
        CaseType, on_delete=models.DO_NOTHING, null=False, blank=False, related_name="OpenGeneralLicence"
    )
    countries = models.ManyToManyField(Country, related_name="OpenGeneralLicence", default=[])
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
