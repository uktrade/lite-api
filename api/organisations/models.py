import uuid

from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from api.addresses.models import Address

from api.audit_trail.enums import AuditType
from api.audit_trail import service as audit_trail_service
from api.common.models import TimestampableModel
from api.core.constants import ExporterPermissions
from api.core.exceptions import NotFoundError
from api.core.helpers import get_exporter_frontend_url
from api.flags.models import Flag
from api.organisations.enums import LocationType, OrganisationDocumentType, OrganisationStatus, OrganisationType
from api.staticdata.countries.models import Country

from api.users.notify import notify_exporter_user_added
from api.users.libraries.get_user import get_user_organisation_relationship
from api.users.models import UserOrganisationRelationship


class Organisation(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    type = models.CharField(
        choices=OrganisationType.choices,
        default=OrganisationType.COMMERCIAL,
        max_length=20,
    )
    status = models.CharField(
        choices=OrganisationStatus.choices,
        default=OrganisationStatus.IN_REVIEW,
        max_length=20,
    )
    eori_number = models.TextField(default=None, blank=True, null=True)
    sic_number = models.TextField(default=None, blank=True, null=True)
    vat_number = models.TextField(default=None, blank=True, null=True)
    registration_number = models.TextField(default=None, blank=True, null=True)
    phone_number = PhoneNumberField(default="")
    website = models.URLField(blank=True, default="")
    primary_site = models.ForeignKey(
        "Site",
        related_name="organisation_primary_site",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
    )
    flags = models.ManyToManyField(Flag, related_name="organisations")

    def get_user_relationship(self, user):
        try:
            user_organisation_relationship = UserOrganisationRelationship.objects.get(user=user, organisation=self)
            return user_organisation_relationship
        except UserOrganisationRelationship.DoesNotExist:
            raise NotFoundError({"user": "User does not belong to this organisation"})

    def get_users(self):
        user_organisation_relationships = UserOrganisationRelationship.objects.filter(organisation=self)

        for relationship in user_organisation_relationships:
            relationship.user.status = relationship.status

        return [x.user for x in user_organisation_relationships]

    def is_active(self):
        return self.status == OrganisationStatus.ACTIVE

    def save(self, **kwargs):
        super().save(**kwargs)
        # Update the primary site's organisation to link them
        if self.primary_site:
            self.primary_site.organisation = self
            self.primary_site.save()

    def notify_exporter_user_added(self, email):
        notify_exporter_user_added(
            email,
            {"organisation_name": self.name, "exporter_frontend_url": get_exporter_frontend_url("/")},
        )

    def add_case_note_add_export_user(self, actor, sites, exporter_email):

        user_org_sites = Site.objects.filter(id__in=sites).values_list("name", flat=True)
        site_names = ",".join(list(user_org_sites))
        audit_trail_service.create(
            actor=actor,
            verb=AuditType.ADD_EXPORTER_USER_TO_ORGANISATION,
            payload={"exporter_email": exporter_email, "site_names": site_names},
            target=self,
        )

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
            ExporterPermissions.ADMINISTER_SITES,
            exporter_user_organisation_relationship.organisation,
        ):
            return self.get_by_organisation(exporter_user_organisation_relationship.organisation)

        return exporter_user_organisation_relationship.sites.all()


class Site(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=False)
    organisation = models.ForeignKey(
        Organisation,
        blank=True,
        null=True,
        related_name="site",
        on_delete=models.CASCADE,
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
        Organisation,
        blank=True,
        null=True,
        related_name="external_location",
        on_delete=models.CASCADE,
    )
    location_type = models.CharField(
        choices=LocationType.choices,
        null=True,
        blank=True,
        max_length=20,
    )
