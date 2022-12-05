from parameterized import parameterized

from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient

from ..enums import RegimesEnum
from ..models import RegimeEntry


class EntriesTests(DataTestClient):
    @parameterized.expand(
        [
            ("mtcr_entries", "mtcr"),
            ("wassenaar_entries", "wassenaar"),
        ]
    )
    def test_redirects(self, url_path, regime_type):
        url = reverse(f"staticdata:regimes:{url_path}")
        response = self.client.get(url)
        self.assertRedirects(
            response,
            reverse(
                "staticdata:regimes:entries",
                kwargs={
                    "regime_type": regime_type,
                },
            ),
            status_code=301,
        )

    def test_entries_invalid_regime_type(self):
        url = reverse(
            "staticdata:regimes:entries",
            kwargs={
                "regime_type": "not-found",
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @parameterized.expand(
        [
            (RegimesEnum.MTCR, "mtcr"),
            (RegimesEnum.WASSENAAR, "wassenaar"),
        ]
    )
    def test_entries_filters_by_regime_type(self, regime_pk, regime_type):
        url = reverse(
            "staticdata:regimes:entries",
            kwargs={
                "regime_type": regime_type,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.json()),
            RegimeEntry.objects.filter(subsection__regime=regime_pk).count(),
        )
