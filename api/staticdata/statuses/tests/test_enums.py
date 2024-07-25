from parameterized import parameterized

from api.staticdata.statuses.enums import CaseStatusEnum


class TestCaseStatusEnum:

    @parameterized.expand(CaseStatusEnum.caseworker_operable_statuses())
    def test_is_caseworker_operable_operable_status_status_operable(self, status):
        assert CaseStatusEnum.is_caseworker_operable(status) is True

    @parameterized.expand(CaseStatusEnum.caseworker_inoperable_statuses())
    def test_is_caseworker_operable_operable_status_status_inoperable(self, status):
        assert CaseStatusEnum.is_caseworker_operable(status) is False
