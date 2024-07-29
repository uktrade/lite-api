import pytest

from django.test import RequestFactory
from parameterized import parameterized

from api.applications.models import BaseApplication
from api.applications.views.applications import ApplicationList
from api.applications.views.filters import ApplicationSiteFilter, ApplicationStateFilter
from api.applications.tests.factories import (
    SiteOnApplicationFactory,
    StandardApplicationFactory,
)
from api.core.authentication import ORGANISATION_ID
from api.core.constants import ExporterPermissions, Roles
from api.core.exceptions import NotFoundError
from api.organisations.models import Site
from api.organisations.tests.factories import OrganisationFactory, SiteFactory
from api.users.models import Permission, Role, UserOrganisationRelationship
from api.users.tests.factories import ExporterUserFactory, UserOrganisationRelationshipFactory
from test_helpers.clients import DataTestClient


class ApplicationFiltersTests(DataTestClient):

    def setUp(self):
        super().setUp()

        self.filter = ApplicationSiteFilter()
        self.view = ApplicationList.as_view()
        self.queryset = BaseApplication.objects.all()

        factory = RequestFactory()

        self.request = factory.get("/")
        self.request.META[ORGANISATION_ID] = self.organisation.id
        self.request.user = self.exporter_user.baseuser_ptr
        self.request.user.exporteruser = self.exporter_user

    @parameterized.expand(
        [
            [4, 2, [], 4],
            [4, 2, [ExporterPermissions.ADMINISTER_SITES.name], 6],
        ]
    )
    def test_exporter_user_only_access_assigned_sites(self, site1_count, site2_count, permissions, expected):
        user_org = UserOrganisationRelationship.objects.get(
            user=self.exporter_user,
            organisation=self.organisation,
            role=Role.objects.get(id=Roles.EXPORTER_EXPORTER_ROLE_ID),
        )
        site = Site.objects.get(organisation=self.organisation)
        site.users.add(user_org)

        # set permissions
        user_org.role.permissions.add(*list(Permission.objects.filter(id__in=permissions)))

        for _ in range(site1_count):
            SiteOnApplicationFactory(
                site=site,
                application=StandardApplicationFactory(organisation=self.organisation),
            )

        # Create additional sites
        another_user_org = UserOrganisationRelationshipFactory(
            user=ExporterUserFactory(), organisation=self.organisation
        )
        another_site = SiteFactory(organisation=self.organisation)
        another_site.users.add(another_user_org)

        for i in range(site2_count):
            SiteOnApplicationFactory(
                site=another_site,
                application=StandardApplicationFactory(organisation=another_user_org.organisation),
            )

        queryset = self.filter.filter_queryset(self.request, self.queryset, self.view)
        self.assertEqual(queryset.count(), expected)

    def test_exporter_user_unauthorized_site_raises_error(self):
        some_other_org = OrganisationFactory()
        self.request.META[ORGANISATION_ID] = some_other_org.id

        StandardApplicationFactory(organisation=self.organisation)

        with pytest.raises(NotFoundError):
            self.filter.filter_queryset(self.request, self.queryset, self.view)
