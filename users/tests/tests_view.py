from django.urls import reverse
from rest_framework import status

from api.conf.helpers import convert_queryset_to_str, date_to_drf_date
from api.organisations.enums import OrganisationStatus
from test_helpers.clients import DataTestClient
from test_helpers.helpers import generate_key_value_pair
from users.libraries.get_user import get_user_organisation_relationship


class UserTests(DataTestClient):
    def test_user_can_view_their_own_profile_info(self):
        """
        Tests the 'users/me' endpoint
        Ensures that the endpoint returns the correct details about the signed in user
        """
        response = self.client.get(reverse("users:me"), **self.exporter_headers)
        response_data = response.json()
        relationship = get_user_organisation_relationship(self.exporter_user, self.organisation)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_data,
            {
                "id": str(self.exporter_user.id),
                "first_name": self.exporter_user.first_name,
                "last_name": self.exporter_user.last_name,
                "organisations": [
                    {
                        "id": str(relationship.organisation.id),
                        "joined_at": date_to_drf_date(relationship.created_at),
                        "name": relationship.organisation.name,
                        "status": generate_key_value_pair(relationship.organisation.status, OrganisationStatus.choices),
                    }
                ],
                "role": {
                    "id": str(relationship.role.id),
                    "permissions": convert_queryset_to_str(relationship.role.permissions.values_list("id", flat=True)),
                },
            },
        )
