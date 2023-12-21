import datetime

from freezegun import freeze_time
from parameterized import parameterized

from django.test import TestCase, override_settings
from django.utils import timezone

from ..tasks import today, yesterday


@override_settings(TIME_ZONE="UTC")
@freeze_time("2020-01-01 12:00:01")
class TodayTestCase(TestCase):
    def test_today_without_time(self):
        output = today()
        self.assertEqual(
            output,
            datetime.datetime(2020, 1, 1, 12, 0, 1, tzinfo=timezone.get_current_timezone()),
        )

    def test_today_with_time(self):
        output = today(time=datetime.time(1, 0, 1))
        self.assertEqual(
            output,
            datetime.datetime(2020, 1, 1, 1, 0, 1, tzinfo=timezone.get_current_timezone()),
        )


@override_settings(TIME_ZONE="UTC")
@freeze_time("2022-07-12 12:00:01")
class YesterdayTestCase(TestCase):
    FRIDAY = datetime.datetime(2022, 7, 8, 12, 0, 1)
    SATURDAY = datetime.datetime(2022, 7, 9, 12, 0, 1)
    SUNDAY = datetime.datetime(2022, 7, 10, 12, 0, 1)

    DAY_BEFORE_BANK_HOLIDAY = datetime.datetime(2020, 12, 24, 12, 0, 1)
    BANK_HOLIDAY = datetime.datetime(2020, 12, 25, 12, 0, 1)

    def test_yesterday(self):
        output = yesterday()
        self.assertEqual(
            output,
            datetime.datetime(2022, 7, 11, 12, 0, 1, tzinfo=timezone.get_current_timezone()),
        )

    def test_yesterday_with_explicit_date(self):
        output = yesterday(
            date=datetime.datetime(2022, 7, 13, 12, 0, 1, tzinfo=timezone.get_current_timezone()),
        )
        self.assertEqual(
            output,
            datetime.datetime(2022, 7, 12, 12, 0, 1, tzinfo=timezone.get_current_timezone()),
        )

    def test_yesterday_with_explicit_time(self):
        output = yesterday(
            date=datetime.datetime(2022, 7, 13, 12, 0, 1, tzinfo=timezone.get_current_timezone()),
            time=datetime.time(1, 0, 1),
        )
        self.assertEqual(
            output,
            datetime.datetime(2022, 7, 12, 1, 0, 1, tzinfo=timezone.get_current_timezone()),
        )

    @parameterized.expand([(SATURDAY,), (SUNDAY,)])
    def test_yesterday_on_weekend(self, date):
        output = yesterday(date=date)
        self.assertEqual(output, self.FRIDAY)

    def test_yesterday_on_bank_holiday(self):
        output = yesterday(date=self.BANK_HOLIDAY)
        self.assertEqual(output, self.DAY_BEFORE_BANK_HOLIDAY)
