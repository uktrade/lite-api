from unittest import mock
from parameterized import parameterized


from api.core.permissions import BULK_APPROVE_ALLOWED_QUEUES, CanCaseworkerBulkApprove, CaseInCaseworkerOperableStatus
from api.applications.tests.factories import StandardApplicationFactory
from api.queues.caseworker.views.bulk_approval import BulkApprovalCreateView
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from lite_routing.routing_rules_internal.enums import QueuesEnum

from test_helpers.clients import DataTestClient


class TestCaseInCaseworkerOperableStatus(DataTestClient):

    @parameterized.expand(CaseStatusEnum.caseworker_operable_statuses())
    def test_has_permission_caseworker_operable(self, status):
        status_record = CaseStatus.objects.get(status=status)
        application = StandardApplicationFactory(status=status_record)
        mock_view = mock.MagicMock()
        mock_view.get_case.return_value = application.get_case()
        permission_obj = CaseInCaseworkerOperableStatus()
        assert permission_obj.has_permission(None, mock_view) is True

    @parameterized.expand(CaseStatusEnum.caseworker_inoperable_statuses())
    def test_has_permission_caseworker_inoperable(self, status):
        status_record = CaseStatus.objects.get(status=status)
        application = StandardApplicationFactory(status=status_record)
        mock_view = mock.MagicMock()
        mock_view.get_case.return_value = application.get_case()
        permission_obj = CaseInCaseworkerOperableStatus()
        assert permission_obj.has_permission(None, mock_view) is False


class TestCanCaseworkerBulkApprove(DataTestClient):

    @parameterized.expand(
        [
            (BULK_APPROVE_ALLOWED_QUEUES["MOD_CAPPROT"], True),
            (BULK_APPROVE_ALLOWED_QUEUES["MOD_DI_DIRECT"], True),
            (BULK_APPROVE_ALLOWED_QUEUES["MOD_DI_INDIRECT"], True),
            (BULK_APPROVE_ALLOWED_QUEUES["MOD_DSR"], True),
            (BULK_APPROVE_ALLOWED_QUEUES["MOD_DSTL"], True),
            (BULK_APPROVE_ALLOWED_QUEUES["NCSC"], True),
            (QueuesEnum.FCDO, False),
            (QueuesEnum.FCDO_COUNTER_SIGNING, False),
            (QueuesEnum.DESNZ_CHEMICAL, False),
            (QueuesEnum.DESNZ_NUCLEAR, False),
        ]
    )
    def test_has_permission_caseworker_bulk_approve(self, queue_id, expected):
        view = BulkApprovalCreateView()
        view.kwargs = {"pk": queue_id}
        permission_obj = CanCaseworkerBulkApprove()
        assert permission_obj.has_permission(None, view) is expected
