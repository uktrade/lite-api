from unittest import mock

from rest_framework import status
from rest_framework.reverse import reverse_lazy

from api.core.constants import Roles
from api.organisations.tests.factories import SiteFactory
from test_helpers.clients import DataTestClient
from api.users.libraries.user_to_token import user_to_token
from api.users.models import ExporterUser


class CreateExporterUser(DataTestClient):
    def setUp(self):
        super().setUp()
        self.site = SiteFactory(organisation=self.organisation)

        self.data = {
            "email": "email@email.com",
            "sites": [str(self.site.id)],
            "role": Roles.EXPORTER_EXPORTER_ROLE_ID,
        }
        self.url = reverse_lazy("users:users")

    @mock.patch("api.users.notify.notify_exporter_user_added")
    def test_create_new_exporter_user_success(self, mocked_notify):
        previous_user_count = ExporterUser.objects.count()

        response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExporterUser.objects.count(), previous_user_count + 1)
        mocked_notify.assert_called_with(
            self.data["email"],
            {
                "organisation_name": self.organisation.name,
                "exporter_frontend_url": "https://exporter.lite.service.localhost.uktrade.digital/",
            },
        )

    @mock.patch("api.users.notify.notify_exporter_user_added")
    def test_create_exporter_user_when_user_already_exists_doesnt_create_new_user(self, mocked_notify):
        """
        The endpoint being tested requires another exporter user to send the request
        This means that the new user being added must be attempted to be added by different exporter users
        as the endpoint attempts to add the new user to the request user's organisation
        """

        # Add new exporter user
        self.client.post(self.url, self.data, **self.exporter_headers)
        # Create another request user before attempting to re-add the new exporter user
        other_org, other_exporter_user = self.create_organisation_with_exporter_user()
        other_exporter_user_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(other_exporter_user.baseuser_ptr),
            "HTTP_ORGANISATION_ID": str(other_org.id),
        }
        previous_user_count = ExporterUser.objects.count()

        response = self.client.post(self.url, self.data, **other_exporter_user_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExporterUser.objects.count(), previous_user_count)
        mocked_notify.assert_called_with(
            self.data["email"],
            {
                "organisation_name": other_org.name,
                "exporter_frontend_url": "https://exporter.lite.service.localhost.uktrade.digital/",
            },
        )

    @mock.patch("api.users.notify.notify_exporter_user_added")
    def test_create_exporter_user_when_user_already_associated_to_organisation(self, mocked_notify):
        # Add new exporter user
        self.client.post(self.url, self.data, **self.exporter_headers)
        previous_user_count = ExporterUser.objects.count()
        # Attempt to add the user to the same org again
        response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExporterUser.objects.count(), previous_user_count)
        # Expect just one notification to have fired (the initial add of this user only)
        assert mocked_notify.call_count == 1

    def test_create_exporter_uppercase_email(self):
        previous_user_count = ExporterUser.objects.count()
        data = {
            "email": "TESTEXPORTER@email.com",
            "phone_number": "+447812346820",
            "sites": [str(self.site.id)],
            "role": Roles.EXPORTER_EXPORTER_ROLE_ID,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExporterUser.objects.count(), previous_user_count + 1)
        self.assertEqual(ExporterUser.objects.filter(baseuser_ptr__email__iexact=data["email"].lower()).count(), 1)
