import pytest

from rest_framework.exceptions import ParseError

from api.cases.generated_documents.helpers import get_draft_licence
from api.cases.enums import AdviceType
from api.applications.tests.factories import StandardApplicationFactory
from api.licences.tests.factories import StandardLicenceFactory
from api.f680.tests.factories import SubmittedF680ApplicationFactory
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.statuses.enums import CaseStatusEnum


pytestmark = pytest.mark.django_db


def test_get_draft_licence_f680_application_returns_none():
    application = SubmittedF680ApplicationFactory()
    assert get_draft_licence(application.case_ptr, AdviceType.APPROVE) is None


def test_get_draft_licence_standard_application_case_finalised_returns_none():
    finalised_status = CaseStatus.objects.get(status=CaseStatusEnum.FINALISED)
    application = StandardApplicationFactory(status=finalised_status)
    assert get_draft_licence(application.case_ptr, AdviceType.APPROVE) is None


def test_get_draft_licence_standard_application_draft_exists_success():
    final_review_status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
    application = StandardApplicationFactory(status=final_review_status)
    draft_licence = StandardLicenceFactory(case=application.case_ptr)
    assert get_draft_licence(application.case_ptr, AdviceType.APPROVE) == draft_licence


def test_get_draft_licence_standard_application_refusal_advice_returns_none():
    final_review_status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
    application = StandardApplicationFactory(status=final_review_status)
    assert get_draft_licence(application.case_ptr, AdviceType.REFUSE) is None


def test_get_draft_licence_standard_application_draft_missing_raises_error():
    final_review_status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
    application = StandardApplicationFactory(status=final_review_status)
    with pytest.raises(ParseError):
        get_draft_licence(application.case_ptr, AdviceType.APPROVE)
