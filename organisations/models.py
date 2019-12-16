import uuid

from django.db import models

from addresses.models import Address
from conf.constants import Roles
from conf.exceptions import NotFoundError
from flags.models import Flag
from organisations.enums import OrganisationType
from static.countries.models import Country
from users.libraries.get_user import get_user_organisation_relationship
from users.models import UserOrganisationRelationship


class Organisation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=True)
    type = models.CharField(choices=OrganisationType.choices, default=OrganisationType.COMMERCIAL, max_length=20,)
    eori_number = models.TextField(default=None, blank=True, null=True)
    sic_number = models.TextField(default=None, blank=True, null=True)
    vat_number = models.TextField(default=None, blank=True, null=True)
    registration_number = models.TextField(default=None, blank=True, null=True)
    primary_site = models.ForeignKey(
        "Site", related_name="organisation_primary_site", on_delete=models.CASCADE, blank=True, null=True, default=None,
    )
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_modified_at = models.DateTimeField(auto_now_add=True, blank=True)
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


class SiteManager(models.Manager):
    def get_by_organisation(self, organisation):
        return self.filter(organisation=organisation).all()

    def get_by_user_and_organisation(self, exporter_user, organisation):
        exporter_user_relationship = get_user_organisation_relationship(exporter_user, organisation)
        return self.get_by_user_and_organisation_relationship(exporter_user_relationship)

    def get_by_user_and_organisation_relationship(self, exporter_user_organisation_relationship):
        # Super users have access to all sites
        if exporter_user_organisation_relationship.role.id == Roles.EXPORTER_SUPER_USER_ROLE_ID:
            return self.get_by_organisation(exporter_user_organisation_relationship.organisation)

        return exporter_user_organisation_relationship.sites.all()


class Site(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=False)
    address = models.ForeignKey(Address, related_name="site", on_delete=models.CASCADE)
    organisation = models.ForeignKey(
        Organisation, blank=True, null=True, related_name="site", on_delete=models.CASCADE,
    )
    users = models.ManyToManyField(UserOrganisationRelationship, related_name="sites")

    objects = SiteManager()


class ExternalLocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default=None, blank=False)
    address = models.TextField(default=None, blank=False)
    country = models.ForeignKey(Country, blank=False, null=False, on_delete=models.CASCADE)
    organisation = models.ForeignKey(
        Organisation, blank=True, null=True, related_name="external_location", on_delete=models.CASCADE,
    )
