from parameterized import parameterized

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus

from test_helpers.clients import DataTestClient


class TestCaseStatus(DataTestClient):

    @parameterized.expand(CaseStatusEnum.caseworker_operable_statuses())
    def test_is_caseworker_operable_operable_status_status_operable(self, status):
        status_record = CaseStatus.objects.get(status=status)
        assert status_record.is_caseworker_operable is True

    @parameterized.expand(CaseStatusEnum.caseworker_inoperable_statuses())
    def test_is_caseworker_operable_operable_status_status_inoperable(self, status):
        status_record = CaseStatus.objects.get(status=status)
        assert status_record.is_caseworker_operable is False
