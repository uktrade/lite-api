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
            "random party",
            "party-address",
            "party!address",
            "party-!.<>/%&*;+'(),.address",
            "party\r\naddress",
        ]
    )
    def test_validate_party_address_valid(self, address):
        serializer = PartySerializer(
            data={"address": address},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())

    @parameterized.expand(
        [
            ("\r\n", "Enter an address"),
            (
                "party\address",
                "Address must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "party-\waddress",
                "Address must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "party_address",
                "Address must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "party$address",
                "Address must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "party@address",
                "Address must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
        ]
    )
    def test_validate_party_address_invalid(self, address, error_message):
        serializer = PartySerializer(
            data={"address": address},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        address_errors = serializer.errors["address"]
        self.assertEqual(len(address_errors), 1)
        self.assertEqual(
            str(address_errors[0]),
            error_message,
        )

    @parameterized.expand(
        [
            "random name",
            "party-name",
            "party!name",
            "party-!.<>/%&*;+'(),.name",
        ]
    )
    def test_validate_party_name_valid(self, name):
        serializer = PartySerializer(
            data={"name": name},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())

    @parameterized.expand(
        [
            (
                "party\aname",
                "Party name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "party-\wname",
                "Party name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "party_name",
                "Party name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "party$name",
                "Party name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
            (
                "party@name",
                "Party name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes",
            ),
        ]
    )
    def test_party_name_invalid(self, name, error_message):
        serializer = PartySerializer(
            data={"name": name},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        serializer_error = serializer.errors["name"]
        self.assertEqual(len(serializer_error), 1)
        self.assertEqual(
            str(serializer_error[0]),
            error_message,
        )
