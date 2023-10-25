import datetime
from unittest import mock
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status

from freezegun import freeze_time
from parameterized import parameterized

from django.test import TestCase, override_settings
from django.utils import timezone

from test_helpers.clients import DataTestClient

from ..tasks import today, update_case_processing_time, yesterday


@override_settings(TIME_ZONE="utc")
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


@override_settings(TIME_ZONE="utc")
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


@freeze_time("2020-01-01 12:00:01")
class ProcessingTimeTest(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)

        self.standard_application_1 = self.create_draft_standard_application(self.organisation)
        self.case_1 = self.submit_application(self.standard_application_1)
        self.standard_application_1.status = get_case_status_by_status(CaseStatusEnum.WITHDRAWN)
        self.standard_application_1.save()

    @mock.patch("api.cases.tasks.get_case_sla")
    def test_update_case_processing_time(self, mock_get_case_sla):
        mock_get_case_sla.return_value = {"sla_days": 2}
        result = update_case_processing_time.now()
        self.case.refresh_from_db()
        self.case_1.refresh_from_db()
        self.assertEqual(result, True)

        self.assertEqual(
            self.case.processing_time,
            2,
        )

        self.assertEqual(
            self.case_1.processing_time,
            0,
        )
