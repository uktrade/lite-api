import uuid

import reversion
from django.db import models

from applications.enums import ApplicationLicenceType, ApplicationExportType
from parties.models import EndUser, UltimateEndUser, Consignee, ThirdParty
from goods.models import Good
from organisations.models import Organisation, Site, ExternalLocation
from static.countries.models import Country
from static.denial_reasons.models import DenialReason
from static.statuses.models import CaseStatus
from static.units.enums import Units


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
    status = models.ForeignKey(CaseStatus, related_name='application_status', on_delete=models.CASCADE, blank=True,
                               null=True)
    licence_type = models.CharField(choices=ApplicationLicenceType.choices, default=None, max_length=50) # this is open or standard lincences
    export_type = models.CharField(choices=ApplicationExportType.choices, default=None, max_length=50)
    reference_number_on_information_form = models.TextField(blank=True, null=True)
    # the person whos buying + they'll be ultimate users too who this end user is selling too
    end_user = models.ForeignKey(EndUser, related_name='application_end_user', on_delete=models.CASCADE,
                                 default=None, blank=True, null=True)
    # destination = models to be a list of countries
    # plus there maybe a consignee too - the person moving the cargo
    ultimate_end_users = models.ManyToManyField(UltimateEndUser, related_name='application_ultimate_end_users')
    consignee = models.ForeignKey(Consignee, related_name='application_consignee', on_delete=models.CASCADE,
                                  default=None, blank=True, null=True)
    third_parties = models.ManyToManyField(ThirdParty, related_name='application_third_parties')


@reversion.register()
class GoodOnApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    good = models.ForeignKey(Good, related_name='goods_on_application', on_delete=models.CASCADE)
    application = models.ForeignKey(Application, related_name='goods', on_delete=models.CASCADE)
    quantity = models.FloatField(null=True, blank=True, default=None)
    unit = models.CharField(choices=Units.choices, default=Units.GRM, max_length=50)
    value = models.DecimalField(max_digits=256, decimal_places=2)


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


@reversion.register()
class ExternalLocationOnApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_location = models.ForeignKey(ExternalLocation, related_name='external_locations_on_application', on_delete=models.CASCADE)
    application = models.ForeignKey(Application, related_name='external_application_sites', on_delete=models.CASCADE)


@reversion.register()
class CountryOnApplication(models.Model):
    """
    Open licence applications export to countries, instead of an end user
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, related_name='application_countries', on_delete=models.CASCADE)
    country = models.ForeignKey(Country, related_name='countries_on_application', on_delete=models.CASCADE)
