from rest_framework import status
from rest_framework.reverse import reverse_lazy

from conf.constants import Roles
from organisations.models import Organisation
from test_helpers.clients import DataTestClient
from users.libraries.user_to_token import user_to_token
from users.models import ExporterUser


class CreateExporterUser(DataTestClient):
    def setUp(self):
        super().setUp()
        self.site, _ = self.create_site("HQ", self.organisation)

        self.data = {
            "email": "email@email.com",
            "sites": [str(self.site.id)],
            "role": Roles.EXPORTER_DEFAULT_ROLE_ID,
        }
        self.url = reverse_lazy("users:users")

    def test_create_new_exporter_user_success(self):
        previous_user_count = ExporterUser.objects.count()

        response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExporterUser.objects.count(), previous_user_count + 1)

    def test_create_exporter_user_when_user_already_exists_doesnt_create_new_user(self):
        """
        The endpoint being tested requires another exporter user to send the request
        This means that the new user being added must be attempted to be added by different exporter users
        as the endpoint attempts to add the new user to the request user's organisation
        """

        # Add new exporter user
        self.client.post(self.url, self.data, **self.exporter_headers)
        # Create another request user before attempting to re-add the new exporter user
        other_org = Organisation.objects.create(name="other org")
        other_exporter_user = self.create_exporter_user(first_name="bah", last_name="humbug", organisation=other_org)
        other_exporter_user_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(other_exporter_user),
            "HTTP_ORGANISATION_ID": str(other_org.id),
        }
        previous_user_count = ExporterUser.objects.count()

        response = self.client.post(self.url, self.data, **other_exporter_user_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExporterUser.objects.count(), previous_user_count)
