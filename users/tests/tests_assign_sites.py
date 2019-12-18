from rest_framework import status
from rest_framework.reverse import reverse_lazy

from conf.constants import ExporterPermissions
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
        self.url = reverse_lazy("users:assign_sites", kwargs={"pk": self.exporter_user_2.id})

    def test_assign_sites(self):
        data = {"sites": [self.site_1.id, self.site_2.id]}

        response = self.client.put(self.url, data, **self.exporter_headers)
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user_2, self.organisation)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user_organisation_relationship.sites.count(), len(data["sites"]))

    def test_assign_sites_doesnt_override_existing_sites(self):
        # Set up the second user with different sites to what exporter_user has
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user_2, self.organisation)
        user_organisation_relationship.sites.set([self.site_4, self.site_5])

        data = {"sites": [self.site_1.id, self.site_2.id]}

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user_organisation_relationship.sites.count(), len(data["sites"]) + 2)

    def test_cannot_assign_user_to_sites_it_doesnt_have_access_to(self):
        data = {"sites": [self.site_4.id]}

        response = self.client.put(self.url, data, **self.exporter_headers)
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user_2, self.organisation)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(user_organisation_relationship.sites.count(), 0)

    def test_user_cannot_be_assigned_to_site_in_another_organisation(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        data = {"sites": [organisation_2.primary_site.id]}

        response = self.client.put(self.url, data, **self.exporter_headers)
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user_2, self.organisation)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(user_organisation_relationship.sites.count(), 0)

    def test_user_cannot_assign_themselves_to_sites(self):
        data = {"sites": [self.site_1.id]}

        response = self.client.put(
            reverse_lazy("users:assign_sites", kwargs={"pk": self.exporter_user.id}), data, **self.exporter_headers
        )
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user, self.organisation)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user_organisation_relationship.sites.count(), 3)

    def test_user_cannot_be_assigned_to_sites_if_they_have_administer_sites_permission(self):
        user_organisation_relationship = get_user_organisation_relationship(self.exporter_user, self.organisation)
        user_organisation_relationship.role.permissions.set([ExporterPermissions.ADMINISTER_SITES.name])
        data = {"sites": [self.site_1.id]}

        response = self.client.put(
            reverse_lazy("users:assign_sites", kwargs={"pk": self.exporter_user.id}), data, **self.exporter_headers
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user_organisation_relationship.sites.count(), 3)
