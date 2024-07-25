from parameterized import parameterized

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus

from test_helpers.clients import DataTestClient


CASEWORKER_OPERABLE_STATUSES = CaseStatusEnum.caseworker_operable_statuses()
CASEWORKER_INOPERABLE_STATUSES = list(set(CaseStatusEnum.all()) - set(CaseStatusEnum.caseworker_operable_statuses()))


class TestCaseStatus(DataTestClient):

    @parameterized.expand(CASEWORKER_OPERABLE_STATUSES)
    def test_is_caseworker_operable_operable_status_status_operable(self, status):
        status_record = CaseStatus.objects.get(status=status)
        assert status_record.is_caseworker_operable is True

    @parameterized.expand(CASEWORKER_INOPERABLE_STATUSES)
    def test_is_caseworker_operable_operable_status_status_inoperable(self, status):
        status_record = CaseStatus.objects.get(status=status)
        assert status_record.is_caseworker_operable is False
