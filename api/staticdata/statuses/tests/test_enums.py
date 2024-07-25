from parameterized import parameterized

from api.staticdata.statuses.enums import CaseStatusEnum


CASEWORKER_OPERABLE_STATUSES = CaseStatusEnum.caseworker_operable_statuses()
CASEWORKER_INOPERABLE_STATUSES = list(set(CaseStatusEnum.all()) - set(CaseStatusEnum.caseworker_operable_statuses()))


class TestCaseStatusEnum:

    @parameterized.expand(CASEWORKER_OPERABLE_STATUSES)
    def test_is_caseworker_operable_operable_status_status_operable(self, status):
        assert CaseStatusEnum.is_caseworker_operable(status) is True

    @parameterized.expand(CASEWORKER_INOPERABLE_STATUSES)
    def test_is_caseworker_operable_operable_status_status_inoperable(self, status):
        assert CaseStatusEnum.is_caseworker_operable(status) is False
