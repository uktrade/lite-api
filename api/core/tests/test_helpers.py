from django.test import override_settings, TestCase
from parameterized import parameterized

from api.core import helpers


class HelpersTest(TestCase):
    @parameterized.expand(
        [
            ("/foo/bar/", "https://caseworker.lite.com/foo/bar/"),
            ("foo/bar/", "https://caseworker.lite.com/foo/bar/"),
        ]
    )
    @override_settings(CASEWORKER_BASE_URL="https://caseworker.lite.com")
    def test_get_caseworker_frontend_url(self, path, expected_url):
        assert helpers.get_caseworker_frontend_url(path) == expected_url

    @parameterized.expand(
        [
            ("/foo/bar/", "https://exporter.lite.com/foo/bar/"),
            ("foo/bar/", "https://exporter.lite.com/foo/bar/"),
        ]
    )
    @override_settings(EXPORTER_BASE_URL="https://exporter.lite.com")
    def test_get_exporter_frontend_url(self, path, expected_url):
        assert helpers.get_exporter_frontend_url(path) == expected_url
