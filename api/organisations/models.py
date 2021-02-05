import uuid

from django.db import models, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from api.addresses.models import Address
from api.common.models import TimestampableModel
from api.core.constants import ExporterPermissions
from api.core.exceptions import NotFoundError
from api.flags.models import Flag
from api.open_general_licences.enums import OpenGeneralLicenceStatus
from api.organisations.enums import LocationType, OrganisationDocumentType, OrganisationStatus, OrganisationType
from api.staticdata.countries.models import Country
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.users.libraries.get_user import get_user_organisation_relationship
from api.users.models import UserOrganisationRelationship


class Organisation(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    type = models.CharField(choices=OrganisationType.choices, default=OrganisationType.COMMERCIAL, max_length=20,)
    status = models.CharField(choices=OrganisationStatus.choices, default=OrganisationStatus.IN_REVIEW, max_length=20,)
    eori_number = models.TextField(default=None, blank=True, null=True)
    sic_number = models.TextField(default=None, blank=True, null=True)
    vat_number = models.TextField(default=None, blank=True, null=True)
    registration_number = models.TextField(default=None, blank=True, null=True)
    primary_site = models.ForeignKey(
        "Site", related_name="organisation_primary_site", on_delete=models.CASCADE, blank=True, null=True, default=None,
    )
    flags = models.ManyToManyField(Flag, related_name="organisations")

    def get_user_relationship(self, user):
        try:
            user_organisation_relationship = UserOrganisationRelationship.objects.get(user=user, organisation=self)
            return user_organisation_relationship
        except UserOrganisationRelationship.DoesNotExist:
            raise NotFoundError({"user": "User does not belong to this organisation"})

    def get_users(self):
        user_organisation_relationships = UserOrganisationRelationship.objects.filter(organisation=self).order_by(
            "user__first_name"
        )

        for relationship in user_organisation_relationships:
            relationship.user.status = relationship.status

        return [x.user for x in user_organisation_relationships]

    def is_active(self):
        return self.status == OrganisationStatus.ACTIVE

    def register_open_general_licence(self, open_general_licence, user):
        from api.open_general_licences.models import OpenGeneralLicenceCase
        from api.compliance.helpers import generate_compliance_site_case

        if open_general_licence.status == OpenGeneralLicenceStatus.DEACTIVATED:
            raise ValidationError(
                {"open_general_licence": ["This open general licence is deactivated and cannot be registered"]}
            )

        if not open_general_licence.registration_required:
            raise ValidationError({"open_general_licence": ["This open general licence does not require registration"]})

        # Only register open general licences for sites in the UK which don't already have that licence registered
        registrations = []
        with transaction.atomic():
            for site in (
                Site.objects.get_by_user_and_organisation(user, self)
                .filter(address__country_id="GB")
                .exclude(open_general_licence_cases__open_general_licence=open_general_licence)
            ):
                case = OpenGeneralLicenceCase.objects.create(
                    open_general_licence=open_general_licence,
                    site=site,
                    case_type=open_general_licence.case_type,
                    organisation=self,
                    status=get_case_status_by_status(CaseStatusEnum.FINALISED),
                    submitted_at=timezone.now(),
                    submitted_by=user,
                )
                generate_compliance_site_case(case)
                registrations.append(case.id)

        return open_general_licence.id, registrations

    def save(self, **kwargs):
        super().save(**kwargs)
        # Update the primary site's organisation to link them
        if self.primary_site:
            self.primary_site.organisation = self
            self.primary_site.save()

    class Meta:
        db_table = "organisation"
        ordering = ["name"]


class DocumentOnOrganisation(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        "documents.Document", related_name="document_on_organisations", on_delete=models.CASCADE
    )
    organisation = models.ForeignKey(Organisation, related_name="document_on_organisations", on_delete=models.CASCADE)
    expiry_date = models.DateField(help_text="Date the document is no longer valid")
    document_type = models.TextField(choices=OrganisationDocumentType.choices)
    reference_code = models.TextField()


class SiteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("address", "address__country")

    def get_by_organisation(self, organisation):
        return self.filter(organisation=organisation)

    def get_by_user_and_organisation(self, exporter_user, organisation):
        exporter_user_relationship = get_user_organisation_relationship(exporter_user, organisation)
        return self.get_by_user_organisation_relationship(exporter_user_relationship)

    def get_by_user_organisation_relationship(self, exporter_user_organisation_relationship):
        # Users with Administer Sites permission have access to all sites
        if exporter_user_organisation_relationship.user.has_permission(
            ExporterPermissions.ADMINISTER_SITES, exporter_user_organisation_relationship.organisation,
        ):
            return self.get_by_organisation(exporter_user_organisation_relationship.organisation)

        return exporter_user_organisation_relationship.sites.all()


class Site(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=False)
    organisation = models.ForeignKey(
        Organisation, blank=True, null=True, related_name="site", on_delete=models.CASCADE,
    )
    users = models.ManyToManyField(UserOrganisationRelationship, related_name="sites")
    address = models.ForeignKey(Address, related_name="site", on_delete=models.DO_NOTHING)
    site_records_located_at = models.ForeignKey("self", related_name="records", on_delete=models.DO_NOTHING, null=True)
    is_used_on_application = models.BooleanField(default=None, null=True)

    objects = SiteManager()

    class Meta:
        db_table = "site"
        ordering = ["name"]


class ExternalLocation(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=False)
    address = models.TextField(default=None, blank=False)
    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.CASCADE)
    organisation = models.ForeignKey(
        Organisation, blank=True, null=True, related_name="external_location", on_delete=models.CASCADE,
    )
    location_type = models.CharField(choices=LocationType.choices, null=True, blank=True, max_length=20,)
