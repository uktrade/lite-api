from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient
from users.enums import UserStatuses
from users.libraries.get_user import get_users_from_organisation
from users.models import UserOrganisationRelationship, ExporterUser


class OrganisationUsersViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("organisations:users", kwargs={"org_pk": self.organisation.id})
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_view_all_users_belonging_to_organisation(self):
        """
        Ensure that a user can see all users belonging to an organisation
        """
        # Create an additional organisation and user to ensure
        # that only users from the first organisation are shown
        self.create_organisation_with_exporter_user("New Org")

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["users"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["status"], UserStatuses.ACTIVE)

    def test_view_user_belonging_to_organisation(self):
        """
        Ensure that a user can see an individual user belonging
        to an organisation
        """
        url = reverse("organisations:user", kwargs={"org_pk": self.organisation.id, "user_pk": self.exporter_user.id})

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["user"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["status"], UserStatuses.ACTIVE)

    def test_cannot_see_users_without_permission(self):
        self.exporter_user.set_role(self.organisation, self.exporter_default_role)
        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_see_user_details_without_permission(self):
        self.exporter_user.set_role(self.organisation, self.exporter_default_role)
        url = reverse(
            "organisations:user",
            kwargs={"org_pk": self.organisation.id, "user_pk": self.exporter_user.id},
        )

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OrganisationUsersCreateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("organisations:users", kwargs={"org_pk": self.organisation.id})
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_add_user_to_organisation_success(self):
        """
        Ensure that a user can be added to an organisation
        """
        data = {
            "first_name": "Matt",
            "last_name": "Berninger",
            "email": "matt.berninger@americanmary.com",
        }

        ExporterUser(first_name=data["first_name"], last_name=data["last_name"], email=data["email"],).save()

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(len(UserOrganisationRelationship.objects.all()), 2)

    def test_add_user_to_another_organisation_success(self):
        """
        Ensure that a user can be added to multiple organisations
        """
        exporter_user_2 = self.create_exporter_user(first_name="Jon", last_name="Smith")

        data = {
            "first_name": exporter_user_2.first_name,
            "last_name": exporter_user_2.last_name,
            "email": exporter_user_2.email,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(get_users_from_organisation(self.organisation)), 2)

    def test_add_existing_user_to_organisation_failure(self):
        """
        Ensure that a user cannot be added twice
        to the same organisation
        """
        data = {
            "first_name": self.exporter_user.first_name,
            "last_name": self.exporter_user.last_name,
            "email": self.exporter_user.email,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "is already a member of this organisation.", response_data["errors"]["email"][0],
        )
        self.assertTrue(len(UserOrganisationRelationship.objects.all()), 1)

    def test_cannot_add_user_without_permission(self):
        self.exporter_user.set_role(self.organisation, self.exporter_default_role)
        data = {}
        initial_users_count = ExporterUser.objects.count()

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ExporterUser.objects.count(), initial_users_count)


class OrganisationUsersUpdateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "organisations:user", kwargs={"org_pk": self.organisation.id, "user_pk": self.exporter_user.id},
        )
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_can_deactivate_user(self):
        """
        Ensure that a user can be deactivated
        """
        exporter_user_2 = self.create_exporter_user(self.organisation)
        url = reverse("organisations:user", kwargs={"org_pk": self.organisation.id, "user_pk": exporter_user_2.id},)

        data = {"status": UserStatuses.DEACTIVATED}

        response = self.client.put(url, data, **self.exporter_headers)
        exporter_user_2_relationship = self.organisation.get_user_relationship(exporter_user_2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(exporter_user_2_relationship.status, data["status"])

    def test_user_cannot_deactivate_themselves(self):
        """
        Ensure that a user can be deactivated
        """
        data = {"status": UserStatuses.DEACTIVATED}

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(UserOrganisationRelationship.objects.get(user=self.exporter_user, organisation=self.organisation).status,
                         UserStatuses.ACTIVE)

    def test_cannot_edit_user_without_permission(self):
        self.exporter_user.set_role(self.organisation, self.exporter_default_role)
        payload_name = "changed name"
        data = {
            "first_name": payload_name
        }

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(self.exporter_user.first_name, payload_name)
