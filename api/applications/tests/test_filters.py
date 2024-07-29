import pytest

from django.test import RequestFactory
from parameterized import parameterized
from urllib.parse import urlencode

from api.applications.models import BaseApplication
from api.applications.views.applications import ApplicationList
from api.applications.views.filters import ApplicationSiteFilter, ApplicationStateFilter
from api.applications.tests.factories import (
    DraftStandardApplicationFactory,
    SiteOnApplicationFactory,
    StandardApplicationFactory,
)
from api.core.authentication import ORGANISATION_ID
from api.core.constants import ExporterPermissions, Roles
from api.core.exceptions import NotFoundError
from api.organisations.models import Site
from api.organisations.tests.factories import OrganisationFactory, SiteFactory
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.users.models import Permission, Role, UserOrganisationRelationship
from api.users.tests.factories import ExporterUserFactory, UserOrganisationRelationshipFactory
from test_helpers.clients import DataTestClient


class ApplicationFiltersTests(DataTestClient):

    def setUp(self):
        super().setUp()

        self.view = ApplicationList.as_view()
        self.queryset = BaseApplication.objects.all()

    def get_request(self, url, params):
        factory = RequestFactory()

        url = f"{url}?{urlencode(params, doseq=True)}"
        request = factory.get(url)
        request.META[ORGANISATION_ID] = self.organisation.id
        request.user = self.exporter_user.baseuser_ptr
        request.user.exporteruser = self.exporter_user

        return request

    @parameterized.expand(
        [
            [4, 2, [], 4],
            [4, 2, [ExporterPermissions.ADMINISTER_SITES.name], 6],
        ]
    )
    def test_exporter_user_only_access_assigned_sites(self, site1_count, site2_count, permissions, expected):
        filter = ApplicationSiteFilter()
        request = self.get_request("/", {})

        # assign user to specific organisation and site
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

        queryset = filter.filter_queryset(request, self.queryset, self.view)
        self.assertEqual(queryset.count(), expected)

    def test_exporter_user_unauthorized_site_raises_error(self):
        filter = ApplicationSiteFilter()

        request = self.get_request("/", {})
        some_other_org = OrganisationFactory()
        request.META[ORGANISATION_ID] = some_other_org.id

        StandardApplicationFactory(organisation=self.organisation)

        with pytest.raises(NotFoundError):
            filter.filter_queryset(request, self.queryset, self.view)

    @parameterized.expand(
        [
            [
                {"num_drafts": 10},
                {"status": "submitted", "count": 2},
                [
                    {"selected_filter": "draft_applications", "expected": 8},
                    {"selected_filter": "submitted_applications", "expected": 2},
                    {"selected_filter": "archived_applications", "expected": 0},
                ],
            ],
            [
                {"num_drafts": 10},
                {"status": "submitted", "count": 4},
                [
                    {"selected_filter": "draft_tab", "expected": 6},
                    {"selected_filter": "submitted_applications", "expected": 4},
                ],
            ],
            [
                {"num_drafts": 10},
                {"status": "finalised", "count": 5},
                [
                    {"selected_filter": "finalised_applications", "expected": 5},
                    {"selected_filter": "draft_applications", "expected": 5},
                ],
            ],
            [
                {"num_drafts": 10},
                {"status": "superseded_by_exporter_edit", "count": 3},
                [
                    {"selected_filter": "archived_applications", "expected": 3},
                    {"selected_filter": "draft_applications", "expected": 7},
                    {"selected_filter": "finalised_applications", "expected": 0},
                ],
            ],
        ]
    )
    def test_exporter_user_see_applications_with_specified_status(self, initial, target_state, filters):
        filter = ApplicationStateFilter()

        drafts = [
            DraftStandardApplicationFactory(
                organisation=self.organisation,
            )
            for _ in range(initial["num_drafts"])
        ]

        for draft in drafts[: target_state["count"]]:
            draft.status = get_case_status_by_status(target_state["status"])
            draft.save()

        for filter_item in filters:
            expected_count = filter_item.pop("expected")
            request = self.get_request("/", filter_item)

            result_queryset = filter.filter_queryset(request, self.queryset, self.view)
            self.assertEqual(result_queryset.count(), expected_count)
