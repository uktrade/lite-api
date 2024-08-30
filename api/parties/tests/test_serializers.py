from parameterized import parameterized

from api.parties.serializers import PartySerializer
from test_helpers.clients import DataTestClient


class TestPartySerializer(DataTestClient):
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
        serializer = PartySerializer(
            data={"website": url_input},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["website"],
            url_output,
        )

    def test_party_serializer_validate_website_invalid(self):
        serializer = PartySerializer(
            data={"website": "invalid@ur&l-i.am"},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        website_errors = serializer.errors["website"]
        self.assertEqual(len(website_errors), 1)
        self.assertEqual(
            str(website_errors[0]),
            "Enter a valid URL.",
        )

    @parameterized.expand(
        [
            "random good",
            "good-name",
            "good!name",
            "good-!.<>/%&*;+'(),.name",
        ]
    )
    def test_validate_goods_name_valid(self, name):
        serializer = PartySerializer(
            data={"name": name},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())

    @parameterized.expand(
        [
            ("\r\n", "Enter a name"),
            (
                "good\rname",
                "Product name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "good\nname",
                "Product name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "good\r\nname",
                "Product name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "good_name",
                "Product name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "good$name",
                "Product name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "good@name",
                "Product name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
        ]
    )
    def test_validate_goods_name_invalid(self, name, error_message):
        serializer = PartySerializer(
            data={"name": name},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        name_errors = serializer.errors["name"]
        self.assertEqual(len(name_errors), 1)
        self.assertEqual(
            str(name_errors[0]),
            error_message,
        )
