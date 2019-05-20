from enum import Enum

from django.db import models
from enumchoicefield import ChoiceEnum, EnumChoiceField
import uuid
import reversion

from goods.models import Good
from organisations.models import Organisation
from quantity.units import Units


class ApplicationStatus(ChoiceEnum):
    submitted = "Submitted"
    more_information_required = "More information required"
    under_review = "Under review"
    resubmitted = "Resubmitted"
    withdrawn = "Withdrawn"
    approved = "Approved"
    declined = "Declined"


class LicenceType(Enum):
    standard_licence = 'Standard Individual Export Licence (SIEL)'
    open_licence = 'Open Individual Export Licence (OIEL)'


class ExportType(Enum):
    permanent = 'Permanent'
    temporary = 'Temporary'


@reversion.register()
class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True, null=True)
    activity = models.TextField(default=None, blank=True, null=True)
    destination = models.TextField(default=None, blank=True, null=True)
    usage = models.TextField(default=None, blank=True, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True)
    status = EnumChoiceField(enum_class=ApplicationStatus, default=ApplicationStatus.submitted)
    licence_type = models.CharField(max_length=255, choices=[(tag.name, tag.value) for tag in LicenceType], default=None)
    export_type = models.CharField(max_length=255, choices=[(tag.name, tag.value) for tag in ExportType], default=None)
    reference_number_on_information_form = models.TextField(blank=True, null=True)


@reversion.register()
class GoodOnApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    good = models.ForeignKey(Good, related_name='goods_on_application', on_delete=models.CASCADE)
    application = models.ForeignKey(Application, related_name='goods', on_delete=models.CASCADE)
    quantity = models.FloatField(null=True, blank=True, default=None)
    unit = EnumChoiceField(enum_class=Units, default=Units.NAR)
    value = models.DecimalField(max_digits=256, decimal_places=2)


@reversion.register()
class Destination(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    application = models.ForeignKey(Application, related_name='destinations', on_delete=models.CASCADE)
