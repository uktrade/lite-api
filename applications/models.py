import uuid

import reversion
from django.db import models
from enumchoicefield import EnumChoiceField

from applications.enums import ApplicationStatus, ApplicationLicenceType, ApplicationExportType
from end_user.models import EndUser
from goods.models import Good
from organisations.models import Organisation, Site
from static.denial_reasons.models import DenialReason
from static.units.units import Units


@reversion.register()
class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True, null=True)
    activity = models.TextField(default=None, blank=True, null=True)
    usage = models.TextField(default=None, blank=True, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True)
    status = models.CharField(choices=ApplicationStatus.choices, default=ApplicationStatus.SUBMITTED, max_length=50)
    licence_type = models.CharField(choices=ApplicationLicenceType.choices, default=None, max_length=50)
    export_type = models.CharField(choices=ApplicationExportType.choices, default=None, max_length=50)
    reference_number_on_information_form = models.TextField(blank=True, null=True)
    end_user = models.ForeignKey(EndUser, related_name='application_end_user', on_delete=models.CASCADE,
                                 default=None, blank=True, null=True)


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


@reversion.register()
class SiteOnApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, related_name='sites_on_application', on_delete=models.CASCADE)
    application = models.ForeignKey(Application, related_name='application_sites', on_delete=models.CASCADE)


@reversion.register()
class ApplicationDenialReason(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, related_name='application_denial_reason', on_delete=models.CASCADE)
    reasons = models.ManyToManyField(DenialReason)
    reason_details = models.TextField(default=None, blank=True, null=True, max_length=2200)
