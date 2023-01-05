import pytest
from parameterized import parameterized

from api.parties.serializers import PartySerializer
from django.core.exceptions import ValidationError


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
def test_party_serializer_validate_website_valid(url_input, url_output):
    assert url_output == PartySerializer.validate_website(url_input)


def test_party_serializer_validate_website_invalid():
    with pytest.raises(ValidationError):
        PartySerializer.validate_website("invalid@ur&l-i.am")
