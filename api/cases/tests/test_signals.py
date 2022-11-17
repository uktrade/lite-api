from unittest import mock

from django.test import override_settings

from api.cases.models import Case
from api.cases.signals import case_post_save_handler
from api.cases.tests.factories import CaseFactory
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
