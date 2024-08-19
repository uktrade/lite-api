from unittest import mock
from parameterized import parameterized

from api.core.permissions import CaseInCaseworkerOperableStatus
from api.applications.tests.factories import StandardApplicationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus

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
