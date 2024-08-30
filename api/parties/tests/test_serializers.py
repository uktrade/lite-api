from parameterized import parameterized

from api.parties.serializers import PartySerializer
from django.core.exceptions import ValidationError
from test_helpers.clients import DataTestClient
from rest_framework.exceptions import ValidationError as DrfValidationError


class TestPartySerializer(DataTestClient):
    def setUp(self):
        super().setUp()
        self.ps = PartySerializer()

    @parameterized.expand(
        [
            ("http://workingexample.com", "http://workingexample.com"),
            ("http://www.workingexample.com", "http://www.workingexample.com"),
            ("http://WWW.workingexample.com", "http://WWW.workingexample.com"),
            ("http://workingexample.com", "http://workingexample.com"),
            ("workingexample.com", "https://workingexample.com"),
            ("HTTPS://workingexample.com", "HTTPS://workingexample.com"),
        ]
    )
    def test_party_serializer_validate_website_valid(self, url_input, url_output):
        self.assertEqual(url_output, self.ps.validate_website(url_input))

    def test_party_serializer_validate_website_invalid(self):
        with self.assertRaises(ValidationError):
            self.ps.validate_website("invalid@ur&l-i.am")

    @parameterized.expand(
        [
            "random good",
            "good-name",
            "good!name",
            "good-!.<>/%&*;+'(),.name",
        ]
    )
    def test_validate_goods_name_valid(self, name):
        self.assertEqual(self.ps.validate_name(name), name)

    @parameterized.expand(
        [
            "\r\n",
            "good_name",
            "good$name",
            "good@name",
        ]
    )
    def test_validate_goods_name_invalid(self, name):
        with self.assertRaises(DrfValidationError):
            self.ps.validate_name(name)
