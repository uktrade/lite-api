import pytest
from parameterized import parameterized

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.applications.libraries.case_status_helpers import get_case_statuses


@pytest.mark.django_db
class TestCaseStatus:
    def test_read_only_status_contains_lu_countersign_statuses(self):
        statuses = get_case_statuses(read_only=True)
        assert CaseStatusEnum.FINAL_REVIEW_COUNTERSIGN in statuses
        assert CaseStatusEnum.FINAL_REVIEW_SECOND_COUNTERSIGN in statuses

    def test_all_status_contains_lu_countersign_statuses(self):
        statuses = CaseStatusEnum.all()
        assert CaseStatusEnum.FINAL_REVIEW_COUNTERSIGN in statuses
        assert CaseStatusEnum.FINAL_REVIEW_SECOND_COUNTERSIGN in statuses
