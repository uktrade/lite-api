import pytest
import unittest

from api.goods import serializers
from test_helpers.helpers import mocked_now


class TestPvGradingDetailsSerializer(unittest.TestCase):
    def test_pv_grading_details_serializer(self):
        serializer_one = serializers.PvGradingDetailsSerializer(data={})

        self.assertEqual(serializer_one.is_valid(), False)
        self.assertEqual("custom_grading" in serializer_one.errors, True)

        serializer_two = serializers.PvGradingDetailsSerializer(data={"custom_grading": "foo"})

        self.assertEqual(serializer_two.is_valid(), False)
        self.assertEqual("custom_grading" in serializer_two.errors, False)


@pytest.mark.parametrize(
    "data,valid,error",
    [
        (
            {
                "section_certificate_date_of_expiry": "2000-01-01",
                "section_certificate_number": "1",
                "certificate_missing": False,
            },
            False,
            "Expiry date must be in the future",
        ),
        (
            {
                "section_certificate_date_of_expiry": "2012-01-01",
                "section_certificate_number": "1",
                "certificate_missing": False,
            },
            True,
            None,
        ),
        (
            {
                "section_certificate_date_of_expiry": "2016-01-01",
                "section_certificate_number": "1",
                "certificate_missing": False,
            },
            False,
            "Expiry date is too far in the future",
        ),
        (
            {
                "section_certificate_date_of_expiry": "2015-01-02",
                "section_certificate_number": "1",
                "certificate_missing": False,
            },
            False,
            "Expiry date is too far in the future",
        ),
    ],
)
@unittest.mock.patch("django.utils.timezone.now", side_effect=mocked_now)
def test_firearms_details_serializer(mock_timezone, data, valid, error):

    serializer = serializers.FirearmGoodDetailsSerializer(data=data)

    assert serializer.is_valid() == valid
    if not valid:
        assert serializer.errors["section_certificate_date_of_expiry"][0] == error
