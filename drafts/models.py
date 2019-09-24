# import uuid
#
# from django.db import models
#
# from applications.enums import ApplicationLicenceType, ApplicationExportType, ApplicationExportLicenceOfficialType
# from parties.models import EndUser, UltimateEndUser, Consignee, ThirdParty
# from goods.models import Good
# from organisations.models import Organisation, Site, ExternalLocation
# from static.countries.models import Country
# from static.units.enums import Units


# class Draft(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.TextField(default=None, blank=True, null=True)
#     activity = models.TextField(default=None, blank=True, null=True)
#     usage = models.TextField(default=None, blank=True, null=True)
#     organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, default=None, null=True)
#     created_at = models.DateTimeField(auto_now_add=True, blank=True)
#     last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)
#     licence_type = models.CharField(choices=ApplicationLicenceType.choices, default=None, max_length=50)
#     export_type = models.CharField(choices=ApplicationExportType.choices, default=None, max_length=50)
#     have_you_been_informed = models.CharField(choices=ApplicationExportLicenceOfficialType.choices, default=None,
#                                               max_length=50)
#     reference_number_on_information_form = models.TextField(blank=True, null=True)
#     end_user = models.ForeignKey(EndUser, related_name='draft_end_user', on_delete=models.CASCADE,
#                                  default=None, blank=True, null=True)
#     ultimate_end_users = models.ManyToManyField(UltimateEndUser, related_name='draft_ultimate_end_users')
#     consignee = models.ForeignKey(Consignee, related_name='draft_consignee', on_delete=models.CASCADE,
#                                   default=None, blank=True, null=True)
#     third_parties = models.ManyToManyField(ThirdParty, related_name='draft_third_parties')
#
#
# class GoodOnDraft(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     good = models.ForeignKey(Good, related_name='goods_on_draft', on_delete=models.CASCADE)
#     draft = models.ForeignKey(Draft, related_name='drafts', on_delete=models.CASCADE)
#     quantity = models.FloatField(null=True, blank=True, default=None)
#     unit = models.CharField(choices=Units.choices, default=Units.GRM, max_length=50)
#     value = models.DecimalField(max_digits=256, decimal_places=2)
#
#
# class SiteOnDraft(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     site = models.ForeignKey(Site, related_name='sites_on_draft', on_delete=models.CASCADE)
#     draft = models.ForeignKey(Draft, related_name='draft_sites', on_delete=models.CASCADE)
#
#
# class ExternalLocationOnDraft(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     draft = models.ForeignKey(Draft, related_name='draft_external_locations', on_delete=models.CASCADE)
#     external_location = models.ForeignKey(ExternalLocation, related_name='external_locations_on_draft',
#                                           on_delete=models.CASCADE)
#
#
# class CountryOnDraft(models.Model):
#     """
#     Open licence applications export to countries, instead of an end user
#     """
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     draft = models.ForeignKey(Draft, related_name='draft_countries', on_delete=models.CASCADE)
#     country = models.ForeignKey(Country, related_name='countries_on_draft', on_delete=models.CASCADE)
