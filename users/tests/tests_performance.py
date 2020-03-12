import timeit

from django.urls import reverse
from test_helpers.clients import DataTestClient


class UsersPerformanceTests(DataTestClient):

    url = reverse("users:me")

    def test_users_me_performance(self):
        """
        Tests the performance of the 'users/me' endpoint
        """
        for i in range(100):
            self.create_organisation_with_exporter_user(exporter_user=self.exporter_user)

        print(timeit.timeit(self.make_users_me_request, number=40))

    def make_users_me_request(self):
        """
        Need to wrap the get in a class method to get 'self' context into timeit
        """
        return self.get(self.url, **self.exporter_headers)
