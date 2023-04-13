from unittest import mock

from django.test import override_settings

from api.cases.models import Case
from api.cases.signals import case_post_save_handler
from api.cases.tests.factories import CaseFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient


class TestSignals(DataTestClient):
    @override_settings(FEATURE_C5_ROUTING_ENABLED=True)
    @mock.patch("api.cases.signals.apply_flagging_rules_to_case")
    def test_case_post_save_handler_status_changed(self, mocked_flagging_func):
        submitted = CaseStatus.objects.get(status="submitted")
        case = CaseFactory(status=submitted)
        case.status = CaseStatus.objects.get(status="initial_checks")
        case_post_save_handler(Case, case)
        assert mocked_flagging_func.called

    @override_settings(FEATURE_C5_ROUTING_ENABLED=True)
    @mock.patch("api.cases.signals.apply_flagging_rules_to_case")
    def test_case_post_save_handler_status_not_changed(self, mocked_flagging_func):
        submitted = CaseStatus.objects.get(status="submitted")
        case = CaseFactory(status=submitted)
        case_post_save_handler(Case, case)
        assert not mocked_flagging_func.called

    @override_settings(FEATURE_C5_ROUTING_ENABLED=True)
    @mock.patch("api.cases.signals.apply_flagging_rules_to_case")
    def test_case_post_save_handler_status_draft(self, mocked_flagging_func):
        submitted = CaseStatus.objects.get(status="submitted")
        case = CaseFactory(status=submitted)
        case.status = CaseStatus.objects.get(status="draft")
        case_post_save_handler(Case, case)
        assert not mocked_flagging_func.called

    @override_settings(FEATURE_C5_ROUTING_ENABLED=True)
    @mock.patch("api.cases.signals.apply_flagging_rules_to_case")
    def test_case_post_save_handler_status_terminal(self, mocked_flagging_func):
        submitted = CaseStatus.objects.get(status="submitted")
        case = CaseFactory(status=submitted)
        case.status = CaseStatus.objects.get(status="finalised")
        case_post_save_handler(Case, case)
        assert not mocked_flagging_func.called

    @override_settings(FEATURE_C5_ROUTING_ENABLED=True)
    @mock.patch("api.cases.signals.apply_flagging_rules_to_case")
    def test_case_post_save_handler_raw(self, mocked_flagging_func):
        submitted = CaseStatus.objects.get(status="submitted")
        case = CaseFactory(status=submitted)
        case.status = CaseStatus.objects.get(status="initial_checks")
        case_post_save_handler(Case, case, raw=True)
        assert not mocked_flagging_func.called

    @override_settings(FEATURE_C5_ROUTING_ENABLED=False)
    @mock.patch("api.cases.signals.apply_flagging_rules_to_case")
    def test_case_post_save_handler_no_flag(self, mocked_flagging_func):
        submitted = CaseStatus.objects.get(status="submitted")
        case = CaseFactory(status=submitted)
        case.status = CaseStatus.objects.get(status="initial_checks")
        case_post_save_handler(Case, case)
        assert not mocked_flagging_func.called

    @override_settings(FEATURE_C5_ROUTING_ENABLED=True)
    @mock.patch("api.cases.signals.apply_flagging_rules_to_case")
    def test_case_post_save_handler_signal_fires(self, mocked_flagging_func):
        submitted = CaseStatus.objects.get(status="submitted")
        # We don't expect the initial save to call flagging rules (since the case is new)
        assert not mocked_flagging_func.called
        case = CaseFactory(status=submitted)
        case.status = CaseStatus.objects.get(status="initial_checks")
        case.save()
        assert mocked_flagging_func.called

    """
    Test if workflow kicked off in first save, not in second and kicked off in third save
    """

    @override_settings(FEATURE_C5_ROUTING_ENABLED=True)
    @mock.patch("api.cases.signals.apply_flagging_rules_to_case")
    def test_case_post_save_handler_multiple_call_two_status_changes(self, mocked_flagging_func):
        submitted = CaseStatus.objects.get(status="submitted")
        case = CaseFactory(status=submitted)
        assert not mocked_flagging_func.called
        case.status = CaseStatus.objects.get(status="initial_checks")
        case.save()
        assert mocked_flagging_func.call_count == 1
        case.save()
        assert mocked_flagging_func.call_count == 1
        case.status = CaseStatus.objects.get(status="ogd_advice")
        case.save()
        assert mocked_flagging_func.call_count == 2

    @override_settings(FEATURE_C5_ROUTING_ENABLED=True)
    @override_settings(FEATURE_COUNTERSIGN_ROUTING_ENABLED=True)
    @mock.patch("api.cases.signals.notify_caseworker_countersign_return")
    @mock.patch("api.cases.signals.apply_flagging_rules_to_case")
    def test_case_post_save_handler_notification(self, mocked_flagging_func, mock_notify_func):
        countersign_status = CaseStatus.objects.get(status=CaseStatusEnum.FINAL_REVIEW_SECOND_COUNTERSIGN)
        case = CaseFactory(status=countersign_status)
        case.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        case.save()
        assert mock_notify_func.called
