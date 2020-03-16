import timeit

from django.urls import reverse
from rest_framework import status

from test_helpers.clients import PerformanceTestClient
from parameterized import parameterized

from django.db import connection


class UsersPerformanceTests(PerformanceTestClient):

    url = reverse("users:me")

    def setUp(self):
        super().setUp()

    @parameterized.expand([(10, 0), (100, 0), (1000, 0)])
    def test_users_me_performance(self, org_count, users):
        """
        Tests the performance of the 'users/me' endpoint
        """
        self.create_organisations_multiple_users(
            required_user=self.exporter_user, organisations=org_count, users_per_org=users
        )
        time = timeit.timeit(self.make_users_me_request, number=1)
        print(f"queries: {len(connection.queries)}")

        print(f"{org_count} orgs with {users} other users each time: {time}")

    def make_users_me_request(self):
        """
        Need to wrap the get in a class method to get 'self' context into timeit
        """
        _, status_code = self.get(self.url, **self.exporter_headers)
        if status_code != status.HTTP_200_OK:
            assert False
