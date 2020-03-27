from django.urls import reverse
from rest_framework import status

from test_helpers.clients import PerformanceTestClient
from parameterized import parameterized


class UsersPerformanceTests(PerformanceTestClient):

    url = reverse("users:me")

    def make_users_me_request(self):
        """
        Need to wrap the get in a class method to get 'self' context into timeit
        """
        response = self.client.get(self.url, **self.exporter_headers)
        self.assertTrue(response.status_code == status.HTTP_200_OK)

    @parameterized.expand([(10, 0), (100, 0), (1000, 0)])
    def test_users_me_performance_by_organisation(self, org_count, users):
        """
        Tests the performance of the 'users/me' endpoint
        """
        self.create_organisations_multiple_users(
            required_user=self.exporter_user, organisations=org_count, users_per_org=users
        )
        print(f"organisations: {org_count}")
        self.timeit(self.make_users_me_request)

    @parameterized.expand([(10, 0), (100, 0), (1000, 0)])
    def test_users_me_performance_by_sites(self, sites, users):
        """
        Tests the performance of the 'users/me' endpoint
        """
        self.create_multiple_sites_for_an_organisation(organisation=self.organisation, sites_count=sites)

        print(f"sites: {sites}")
        self.timeit(self.make_users_me_request)

    @parameterized.expand([(1, 10), (1, 100), (1, 1000)])
    def test_users_me_performance_by_users_per_site(self, sites, users):
        """
        Tests the performance of the 'users/me' endpoint
        """
        print(f"users: {users}")
        self.create_multiple_sites_for_an_organisation(
            organisation=self.organisation, sites_count=1, users_per_site=users
        )
        self.timeit(self.make_users_me_request)
