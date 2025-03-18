from api.users.models import ExporterUser, UserOrganisationRelationship
from parameterized import parameterized

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from unittest import mock

from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from api.applications.tests.factories import OrganisationFactory


from test_helpers.clients import DataTestClient
from api.core.constants import GovPermissions, Roles
from uuid import uuid4
from faker import Faker


class TestAddExporterUserToOrganisation(DataTestClient):

    def setUp(self):
        super().setUp()
        self.faker = Faker()
        self.organisation = OrganisationFactory()
        self.url = reverse(
            "caseworker_organisations:exporter_user",
            kwargs={
                "org_pk": self.organisation.id,
            },
        )
        self.data = {
            "role": Roles.EXPORTER_ADMINISTRATOR_ROLE_ID,
            "email": self.faker.unique.email(),
            "sites": [self.organisation.primary_site.id],
            "phone_number": "+441234567895",
        }
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_ORGANISATIONS.name])

    @override_settings(EXPORTER_BASE_URL="https://exporter.lite.example.com")
    @mock.patch("api.organisations.models.notify_exporter_user_added")
    def test_create_exporter_user_success(self, mocked_notify):

        previous_count = ExporterUser.objects.count()

        response = self.client.post(self.url, **self.gov_headers, data=self.data)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["email"], self.data["email"])

        self.assertEqual(ExporterUser.objects.count(), previous_count + 1)
        mocked_notify.assert_called_with(
            self.data["email"],
            {
                "organisation_name": self.organisation.name,
                "exporter_frontend_url": "https://exporter.lite.example.com/",
            },
        )

        user_org_sites = UserOrganisationRelationship.objects.get(
            organisation_id=self.organisation.id, sites__in=self.data["sites"]
        )
        site_names_list = list(user_org_sites.sites.values_list("name", flat=True))
        site_names = ",".join(site_names_list)

        audit_entry = Audit.objects.get(verb=AuditType.ADD_EXPORTER_USER_TO_ORGANISATION)
        self.assertEqual(
            audit_entry.payload,
            {"exporter_email": self.data["email"], "site_names": site_names},
        )

    @parameterized.expand(
        [
            ("sites", ["12345"], {"sites": ["“12345” is not a valid UUID."]}),
            ("email", "", {"email": ["This field may not be blank."]}),
        ]
    )
    def test_create_exporter_user_bad_data(self, key, data_value, expected_error):
        self.data[key] = data_value
        response = self.client.post(self.url, **self.gov_headers, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], expected_error)

    def test_create_exporter_user_organisation_not_found(self):
        self.url = reverse(
            "caseworker_organisations:exporter_user",
            kwargs={
                "org_pk": uuid4(),
            },
        )
        response = self.client.post(self.url, **self.gov_headers, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_exporter_user_no_permision(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_FLAGGING_RULES.name])
        response = self.client.post(self.url, **self.gov_headers, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_exporter_user_exporter_user_not_allowed(self):
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_FLAGGING_RULES.name])
        response = self.client.post(self.url, **self.exporter_headers, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
