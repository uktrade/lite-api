from datetime import time, datetime
from unittest import mock
from unittest.mock import patch

from django.conf import settings
from django.utils import timezone
from parameterized import parameterized
from pytz import timezone as tz

from api.cases.enums import CaseTypeSubTypeEnum
from api.cases.models import Case, CaseQueue, EcjuQuery
from api.cases.celery_tasks import (
    update_cases_sla,
    STANDARD_APPLICATION_TARGET_DAYS,
    OPEN_APPLICATION_TARGET_DAYS,
    SLA_UPDATE_CUTOFF_TIME,
)
from api.cases.models import CaseQueue, DepartmentSLA
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.teams.models import Department
from test_helpers.clients import DataTestClient

HOUR_BEFORE_CUTOFF = time(SLA_UPDATE_CUTOFF_TIME.hour - 1, 0, 0)
HOUR_AFTER_CUTOFF = time(SLA_UPDATE_CUTOFF_TIME.hour + 1, 0, 0)

TODAY = datetime(2020, 2, 12)
YESTERDAY = datetime(2020, 2, 11)


def _set_submitted_at(case, time, date=timezone.localtime()):
    case.submitted_at = datetime.combine(date, time, tzinfo=tz(settings.TIME_ZONE))
    case.save()


def run_update_cases_sla_task():
    return update_cases_sla.apply().get()


class SlaCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case_types = {
            CaseTypeSubTypeEnum.STANDARD: self.create_draft_standard_application(self.organisation),
            CaseTypeSubTypeEnum.OPEN: self.create_draft_open_application(self.organisation),
            CaseTypeSubTypeEnum.GOODS: self.create_clc_query("abc", self.organisation),
            CaseTypeSubTypeEnum.EUA: self.create_end_user_advisory("abc", "abc", self.organisation),
        }

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_sla_update_standard_application(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        application_type=CaseTypeSubTypeEnum.STANDARD,
        target=STANDARD_APPLICATION_TARGET_DAYS,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        application = self.case_types[application_type]
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)

        self.assertEqual(case.sla_remaining_days, target - 1)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_sla_update_open_application(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        application_type=CaseTypeSubTypeEnum.OPEN,
        target=OPEN_APPLICATION_TARGET_DAYS,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        application = self.case_types[application_type]
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, target - 1)

    @parameterized.expand([(CaseTypeSubTypeEnum.GOODS,), (CaseTypeSubTypeEnum.EUA,)])
    def test_sla_doesnt_update_queries(self, query_type):
        query = self.case_types[query_type]
        case = self.submit_application(query)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)
        self.assertEqual(case.sla_remaining_days, None)


class SlaRulesTests(DataTestClient):
    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_sla_cutoff_window(self, mock_is_weekend, mock_is_bank_holiday):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        times = [HOUR_BEFORE_CUTOFF, SLA_UPDATE_CUTOFF_TIME, HOUR_AFTER_CUTOFF]
        for submit_time in times:
            application = self.create_draft_standard_application(self.organisation)
            case = self.submit_application(application)
            _set_submitted_at(case, submit_time)

        results = run_update_cases_sla_task()
        cases = Case.objects.all().order_by("submitted_at")

        self.assertEqual(results, 1)
        self.assertEqual(cases[0].sla_days, 1)
        self.assertEqual(cases[1].sla_days, 0)
        self.assertEqual(cases[2].sla_days, 0)

    def test_sla_ignores_previously_finalised_cases(self):
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        case.last_closed_at = timezone.now()
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    def test_sla_does_not_apply_sla_twice_in_one_day(self):
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        case.sla_updated_at = timezone.now()
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_unanswered_ecju_queries_today_before_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        created_at=datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        self.create_ecju_query(case)
        EcjuQuery.objects.all().update(created_at=created_at)

        with patch(
            "api.cases.celery_tasks.today",
            return_value=datetime.combine(TODAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_unanswered_ecju_queries_today_after_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        created_at=datetime.combine(TODAY, time=HOUR_AFTER_CUTOFF, tzinfo=timezone.utc),
        expected_results=1,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        self.create_ecju_query(case)
        EcjuQuery.objects.all().update(created_at=created_at)

        with patch(
            "api.cases.celery_tasks.today",
            return_value=datetime.combine(TODAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_unanswered_ecju_queries_yesterday_before_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        created_at=datetime.combine(YESTERDAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        self.create_ecju_query(case)
        EcjuQuery.objects.all().update(created_at=created_at)

        with patch(
            "api.cases.celery_tasks.today",
            return_value=datetime.combine(TODAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_unanswered_ecju_queries_yesterday_after_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        created_at=datetime.combine(YESTERDAY, time=HOUR_AFTER_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        self.create_ecju_query(case)
        EcjuQuery.objects.all().update(created_at=created_at)

        with patch(
            "api.cases.celery_tasks.today",
            return_value=datetime.combine(TODAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_answered_ecju_queries_today_before_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        responded_at=datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        query = self.create_ecju_query(case)
        query.created_at = datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc)
        query.responded_at = responded_at
        query.save()

        with patch(
            "api.cases.celery_tasks.yesterday",
            return_value=datetime.combine(YESTERDAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_answered_ecju_queries_today_after_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        responded_at=datetime.combine(TODAY, time=HOUR_AFTER_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        query = self.create_ecju_query(case)
        query.created_at = datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc)
        query.responded_at = responded_at
        query.save()

        with patch(
            "api.cases.celery_tasks.yesterday",
            return_value=datetime.combine(YESTERDAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_answered_ecju_queries_yesterday_before_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        responded_at=datetime.combine(YESTERDAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        query = self.create_ecju_query(case)
        query.created_at = datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc)
        query.responded_at = responded_at
        query.save()

        with patch(
            "api.cases.celery_tasks.yesterday",
            return_value=datetime.combine(YESTERDAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_answered_ecju_queries_yesterday_after_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        responded_at=datetime.combine(YESTERDAY, time=HOUR_AFTER_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        query = self.create_ecju_query(case)
        query.created_at = datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc)
        query.responded_at = responded_at
        query.save()

        with patch(
            "api.cases.celery_tasks.yesterday",
            return_value=datetime.combine(YESTERDAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    @mock.patch("api.cases.celery_tasks.get_case_ids_with_active_ecju_queries")
    def test_update_cases_sla_exception_handling(
        self,
        mock_case_ids,
        mock_is_bank_holiday,
        mock_is_weekend,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False

        def exception_side_effect(*args):
            raise Exception()

        mock_case_ids.side_effect = exception_side_effect
        case = self.create_standard_application_case(self.organisation)
        sla_days_before_task_run = case.sla_days
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = run_update_cases_sla_task()
        case.refresh_from_db()

        self.assertEqual(results, False)
        self.assertEqual(case.sla_days, sla_days_before_task_run)


class WorkingDayTests(DataTestClient):
    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_weekends_ignored(self, weekend_func, bank_holiday_func):
        weekend_func.return_value = True
        bank_holiday_func.return_value = False

        result = run_update_cases_sla_task()

        self.assertFalse(result)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_bank_holidays_ignored(self, weekend_func, bank_holiday_func):
        weekend_func.return_value = False
        bank_holiday_func.return_value = True

        result = run_update_cases_sla_task()

        self.assertFalse(result)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_bank_holiday_weekend_ignored(self, weekend_func, bank_holiday_func):
        weekend_func.return_value = False
        bank_holiday_func.return_value = False

        result = run_update_cases_sla_task()

        # Expecting update_cases_sla to be ran, but no cases found
        self.assertEqual(result, 0)


class TerminalCaseSlaTests(DataTestClient):
    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_sla_not_update_for_terminal(self, mock_is_weekend, mock_is_bank_holiday):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = run_update_cases_sla_task()
        case.refresh_from_db()
        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, STANDARD_APPLICATION_TARGET_DAYS - 1)

        for case_status in CaseStatusEnum.terminal_statuses():
            application.status = get_case_status_by_status(case_status)
            application.save()

            results = run_update_cases_sla_task()
            case.refresh_from_db()
            self.assertEqual(results, 0)
            self.assertEqual(case.sla_days, 1)
            self.assertEqual(case.sla_remaining_days, STANDARD_APPLICATION_TARGET_DAYS - 1)


class DepartmentSLATests(DataTestClient):
    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_department_sla_updated(self, mock_is_weekend, mock_is_bank_holiday):
        # The following is to ensure that this test doesn't fail on
        # non-working days.
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        # Create & submit an application
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        # Assign the application to our team
        CaseQueue.objects.create(case=case, queue=self.queue)
        # Create a test department
        test_department = Department(name="test")
        test_department.save()
        # In order to move the department SLA counter, we need to assign
        # our team to a department
        self.team.department = test_department
        self.team.save()
        run_update_cases_sla_task()
        department_sla = DepartmentSLA.objects.get(department=test_department)
        self.assertEqual(department_sla.sla_days, 1)

    @mock.patch("api.cases.celery_tasks.is_weekend")
    @mock.patch("api.cases.celery_tasks.is_bank_holiday")
    def test_department_sla_updated_across_multiple_teams(self, mock_is_weekend, mock_is_bank_holiday):
        # The following is to ensure that this test doesn't fail on
        # non-working days.
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        # Create & submit an application
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        # Assign the application to our team
        CaseQueue.objects.create(case=case, queue=self.queue)
        # Create a test department
        test_department = Department(name="test_department")
        test_department.save()
        # In order to move the department SLA counter, we need to assign
        # our team to a department
        self.team.department = test_department
        self.team.save()

        # Assign the application to another team that belongs to the same department
        test_team = self.create_team("test_team")
        test_queue = self.create_queue("test_queue", test_team)
        test_team.department = test_department
        test_team.save()
        CaseQueue.objects.create(case=case, queue=test_queue)

        run_update_cases_sla_task()

        # We only expect the SLA counter to have been updated once for the two
        # teams that are both associated with 'test_department'
        test_department_sla = DepartmentSLA.objects.get(department=test_department)
        self.assertEqual(test_department_sla.sla_days, 1)
