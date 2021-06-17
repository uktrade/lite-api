import unittest
import pytest

from test_helpers.helpers import mocked_now

from api.organisations import serializers
from api.organisations.enums import OrganisationDocumentType


@pytest.mark.parametrize(
    "data,valid,error",
    [
        (
            {
                "expiry_date": "2000-01-01",
                "document": {"name": "a-document", "s3_key": "a-document", "size": 476},
                "document_type": OrganisationDocumentType.REGISTERED_FIREARM_DEALER_CERTIFICATE,
                "reference_code": "1234",
            },
            False,
            "Expiry date must be in the future",
        ),
        (
            {
                "expiry_date": "2012-01-01",
                "document": {"name": "a-document", "s3_key": "a-document", "size": 476},
                "document_type": OrganisationDocumentType.REGISTERED_FIREARM_DEALER_CERTIFICATE,
                "reference_code": "1234",
            },
            True,
            None,
        ),
        (
            {
                "expiry_date": "2016-01-01",
                "document": {"name": "a-document", "s3_key": "a-document", "size": 476},
                "document_type": OrganisationDocumentType.REGISTERED_FIREARM_DEALER_CERTIFICATE,
                "reference_code": "1234",
            },
            False,
            "Expiry date is too far in the future",
        ),
        (
            {
                "expiry_date": "2015-01-02",
                "document": {"name": "a-document", "s3_key": "a-document", "size": 476},
                "document_type": OrganisationDocumentType.REGISTERED_FIREARM_DEALER_CERTIFICATE,
                "reference_code": "1234",
            },
            False,
            "Expiry date is too far in the future",
        ),
    ],
)
@unittest.mock.patch("django.utils.timezone.now", side_effect=mocked_now)
def test_document_on_organisation_serializer(mock_timezone, data, valid, error):

    serializer = serializers.DocumentOnOrganisationSerializer(data=data)

    assert serializer.is_valid() == valid
    if not valid:
        assert serializer.errors["expiry_date"][0] == error
