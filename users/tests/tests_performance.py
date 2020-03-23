import timeit

from django.urls import reverse
from rest_framework import status

from test_helpers.clients import PerformanceTestClient
from parameterized import parameterized

from django.db import connection


class UsersPerformanceTests(PerformanceTestClient):

    url = reverse("users:me")

    def make_users_me_request(self):
        """
        Need to wrap the get in a class method to get 'self' context into timeit
        """
        _, status_code = self.get(self.url, **self.exporter_headers)
        self.assertTrue(status_code == status.HTTP_200_OK)

    @parameterized.expand([(10, 0), (100, 0), (1000, 0)])
    def test_users_me_performance_by_organisation(self, org_count, users):
        """
        Tests the performance of the 'users/me' endpoint
        """
        self.create_organisations_multiple_users(
            required_user=self.exporter_user, organisations=org_count, users_per_org=users
        )
        time = timeit.timeit(self.make_users_me_request, number=1)
        print(f"queries: {len(connection.queries)}")

        print(f"{org_count} orgs with {users} other users each time: {time}")

    @parameterized.expand([(10, 0), (100, 0), (1000, 0)])
    def test_users_me_performance_by_sites(self, sites, users):
        """
        Tests the performance of the 'users/me' endpoint
        """
        self.create_multiple_sites_for_an_organisation(organisation=self.organisation, sites_count=sites)
        time = timeit.timeit(self.make_users_me_request, number=1)
        print(f"queries: {len(connection.queries)}")
        print(f"sites: {sites} time: {time}")

    @parameterized.expand([(1, 10), (1, 100), (1, 1000)])
    def test_users_me_performance_by_users(self, sites, users):
        """
        Tests the performance of the 'users/me' endpoint
        """
        self.create_multiple_sites_for_an_organisation(
            organisation=self.organisation, sites_count=1, users_per_site=users
        )
        time = timeit.timeit(self.make_users_me_request, number=1)
        print(f"queries: {len(connection.queries)}")
        print(f"users: {users} time: {time}")
