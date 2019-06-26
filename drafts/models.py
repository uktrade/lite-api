import uuid

from django.db import models
from enumchoicefield import EnumChoiceField

from applications.enums import ApplicationLicenceType, ApplicationExportType, ApplicationExportLicenceOfficialType
from end_user.models import EndUser
from goods.models import Good
from organisations.models import Organisation, Site, ExternalLocation
from static.units.units import Units


class Draft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True, null=True)
    activity = models.TextField(default=None, blank=True, null=True)
    usage = models.TextField(default=None, blank=True, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)
    licence_type = models.CharField(choices=ApplicationLicenceType.choices, default=None, max_length=50)
    export_type = models.CharField(choices=ApplicationExportType.choices, default=None, max_length=50)
    have_you_been_informed = models.CharField(choices=ApplicationExportLicenceOfficialType.choices, default=None, max_length=50)
    reference_number_on_information_form = models.TextField(blank=True, null=True)
    end_user = models.ForeignKey(EndUser, related_name='draft_end_user', on_delete=models.CASCADE,
                                 default=None, blank=True, null=True)


class GoodOnDraft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    good = models.ForeignKey(Good, related_name='goods_on_draft', on_delete=models.CASCADE)
    draft = models.ForeignKey(Draft, related_name='drafts', on_delete=models.CASCADE)
    quantity = models.FloatField(null=True, blank=True, default=None)
    unit = EnumChoiceField(enum_class=Units, default=Units.NAR)
    value = models.DecimalField(max_digits=256, decimal_places=2)


class SiteOnDraft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, related_name='sites_on_draft', on_delete=models.CASCADE)
    draft = models.ForeignKey(Draft, related_name='draft_sites', on_delete=models.CASCADE)


class ExternalLocationOnDraft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draft = models.ForeignKey(Draft, related_name='draft_external_locations', on_delete=models.CASCADE)
    external_location = models.ForeignKey(ExternalLocation, related_name='external_locations_on_draft', on_delete=models.CASCADE)