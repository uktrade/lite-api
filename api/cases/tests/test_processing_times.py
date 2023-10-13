import datetime
import pytest
from parameterized import parameterized

from django.test import TestCase, override_settings
from test_helpers.clients import DataTestClient
from ..processing_times import get_processing_times


@override_settings(TIME_ZONE="utc")
class CaseSLATestCase(DataTestClient):
    FRIDAY = datetime.datetime(2022, 7, 8, 12, 0, 1)
    SATURDAY = datetime.datetime(2022, 7, 9, 12, 0, 1)
    SUNDAY = datetime.datetime(2022, 7, 10, 12, 0, 1)

    DAY_BEFORE_BANK_HOLIDAY = datetime.datetime(2020, 12, 24, 12, 0, 1)
    BANK_HOLIDAY = datetime.datetime(2020, 12, 25, 12, 0, 1)

    @pytest.mark.django_db
    def test_get_processing_times(self):
        expected_assigned = 79
        expected_department = 79
        reference_code = "GBSIEL/2022/0000149/P"
        assigned, deparment = get_processing_times(reference_code)
        self.assertEqual(assigned, expected_assigned)
        self.assertEqual(deparment, expected_department)

    # @parameterized.expand([(SATURDAY,), (SUNDAY,)])
    # def test_yesterday_on_weekend(self, date):
    #     output = yesterday(date=date)
    #     self.assertEqual(output, self.FRIDAY)
