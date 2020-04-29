from django.test import tag
from django.urls import reverse
from rest_framework import status

from test_helpers.clients import PerformanceTestClient
from parameterized import parameterized


@tag("performance-queues")
class QueuesPerformanceTests(PerformanceTestClient):
    def _make_queue_request(self):
        """
        Need to wrap the get in a class method to get 'self' context into timeit
        """
        url = reverse("cases:search") + f"?queue_id={self.queue.id}"
        print(f"url: {url}")
        response = self.client.get(url, **self.gov_headers)
        self.assertTrue(response.status_code == status.HTTP_200_OK)

    @parameterized.expand(
        [(1, 1, 1, 1), (25, 25, 25, 25), (25, 0, 25, 0), (25, 0, 0, 25), (25, 0, 25, 25),]
    )
    def test_queue_case_ordering_performance(
        self, std_cases, open_cases, hmrc_queries_goods_gone, hmrc_queries_goods_in_uk
    ):
        """
        Test various combinations of case/application types to ensure acceptable performance on non-system
        queue page or highlight areas for concern
        """
        self.create_assorted_cases(std_cases, open_cases, hmrc_queries_goods_gone, hmrc_queries_goods_in_uk)
        self.timeit(self._make_queue_request)
