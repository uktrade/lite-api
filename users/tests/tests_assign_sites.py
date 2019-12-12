from django.test import tag
from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from users.libraries.get_user import get_user_organisation_relationship


class AssignSitesTest(DataTestClient):

    def setUp(self):
        super(AssignSitesTest, self).setUp()
        self.site_1, _ = self.create_site("HQ 2", self.organisation)
        self.site_2, _ = self.create_site("HQ 3", self.organisation)
        self.site_3, _ = self.create_site("HQ 4", self.organisation)
        self.site_4, _ = self.create_site("HQ 5", self.organisation)
        self.site_5, _ = self.create_site("HQ 6", self.organisation)

        # Add default sites to the initial user
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user, self.organisation)
        user_organisation_relationship.sites.set([self.site_1, self.site_2, self.site_3])

        self.exporter_user_2 = self.create_exporter_user(self.organisation)
        self.url = reverse("users:assign_sites", kwargs={"pk": self.exporter_user_2.id})

    @tag('only')
    def test_assign_sites(self):
        data = {"sites": [
            self.site_1.id,
            self.site_2.id
        ]}

        response = self.client.put(self.url, data, **self.exporter_headers)
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user_2, self.organisation)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user_organisation_relationship.sites.count(), len(data["sites"]))

    @tag('only')
    def test_assign_sites_doesnt_override_existing_sites(self):
        # Set up the second user with different sites to what exporter_user has
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user_2, self.organisation)
        user_organisation_relationship.sites.set([self.site_4, self.site_5])

        data = {"sites": [
            self.site_1.id,
            self.site_2.id
        ]}

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user_organisation_relationship.sites.count(), len(data["sites"]) + 2)

    @tag('only')
    def test_cannot_assign_user_to_sites_it_doesnt_have_access_to(self):
        data = {"sites": [
            self.site_4.id
        ]}

        response = self.client.put(self.url, data, **self.exporter_headers)
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user_2, self.organisation)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(user_organisation_relationship.sites.count(), 0)

    @tag('only')
    def test_user_cannot_be_assigned_to_site_in_another_organisation(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        data = {"sites": [
            organisation_2.primary_site_id
        ]}

        response = self.client.put(self.url, data, **self.exporter_headers)
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user_2, self.organisation)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(user_organisation_relationship.sites.count(), 0)

    # TODO
    # User cannot assign themselves to sites

    # TODO
    # Test that a superuser cannot be assigned to sites - as they have access to all sites

    # TODO
    # User with "Administer sites" permission has access to ALL sites
    # Write a test around this
