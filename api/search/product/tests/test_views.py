from test_helpers.clients import DataTestClient

from django.urls import reverse


class MoreLikeThisViewTests(DataTestClient):
    def test_more_like_this_404(self):
        url = reverse("more_like_this", kwargs={"pk": "a1e4d94f-8519-4ef3-8863-e8fa17bdd685"})

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
