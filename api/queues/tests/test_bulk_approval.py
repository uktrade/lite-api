import pytest

from django.urls import reverse

from api.applications.models import StandardApplication
from api.applications.tests.factories import DraftStandardApplicationFactory
from api.cases.enums import AdviceLevel, AdviceType
from api.flags.models import Flag
from api.queues.views.bulk_approval import BULK_APPROVAL_FLAG_ID
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus

from lite_routing.routing_rules_internal.enums import QueuesEnum, TeamIdEnum

pytestmark = pytest.mark.django_db


@pytest.fixture
def fcdo_bulk_approval_url():
    return reverse("queues:bulk_approval", kwargs={"pk": QueuesEnum.FCDO})


@pytest.fixture
def fcdo_bulk_countersign_approval_url():
    return reverse("queues:bulk_countersign_approval", kwargs={"pk": QueuesEnum.FCDO_COUNTER_SIGNING})


@pytest.fixture
def multiple_cases_ogd_queue(organisation):
    ogd_advice = CaseStatus.objects.get(status=CaseStatusEnum.OGD_ADVICE)
    cases = [DraftStandardApplicationFactory(organisation=organisation, status=ogd_advice) for i in range(4)]
    for case in cases:
        case.queues.add(*[QueuesEnum.FCDO])

    return cases


def case_subjects(case):
    application = StandardApplication.objects.get(id=case.id)
    return list(application.goods.all()) + list(application.parties.all())


def test_user_bulk_approves_cases(api_client, gov_headers, fcdo_bulk_approval_url, multiple_cases_ogd_queue):
    data = {
        "case_ids": [str(case.id) for case in multiple_cases_ogd_queue],
        "advice": {
            "text": "No concerns",
            "proviso": "",
            "note": "",
            "footnote_required": False,
            "footnote": "",
            "team": TeamIdEnum.FCDO,
        },
    }
    response = api_client.post(fcdo_bulk_approval_url, data=data, **gov_headers)
    assert response.status_code == 201

    bulk_approved_flag = Flag.objects.get(id=BULK_APPROVAL_FLAG_ID)

    for case in multiple_cases_ogd_queue:
        assert case.advice.filter(
            level=AdviceLevel.USER,
            type=AdviceType.APPROVE,
        ).count() == len(case_subjects(case))

        assert QueuesEnum.FCDO not in [str(queue.id) for queue in case.queues.all()]
        assert QueuesEnum.FCDO_COUNTER_SIGNING in [str(queue.id) for queue in case.queues.all()]
        assert bulk_approved_flag in case.flags.all()


def test_user_bulk_countersign_approves_cases(
    api_client,
    fcdo_officer,
    fcdo_officer_headers,
    fcdo_countersigner,
    fcdo_countersigner_headers,
    fcdo_bulk_approval_url,
    fcdo_bulk_countersign_approval_url,
    multiple_cases_ogd_queue,
):
    data = {
        "case_ids": [str(case.id) for case in multiple_cases_ogd_queue],
        "advice": {
            "text": "No concerns",
            "proviso": "",
            "note": "",
            "footnote_required": False,
            "footnote": "",
            "team": TeamIdEnum.FCDO,
        },
    }
    response = api_client.post(fcdo_bulk_approval_url, data=data, **fcdo_officer_headers)
    assert response.status_code == 201

    data = {
        "case_ids": [str(case.id) for case in multiple_cases_ogd_queue],
        "advice": {
            "countersign_comments": "Agree with the recommendation",
            "countersigned_by": str(fcdo_countersigner.baseuser_ptr.id),
            "team": TeamIdEnum.FCDO,
        },
    }
    response = api_client.put(fcdo_bulk_countersign_approval_url, data=data, **fcdo_officer_headers)
    assert response.status_code == 200

    for case in multiple_cases_ogd_queue:
        assert case.advice.filter(
            level=AdviceLevel.USER,
            type=AdviceType.APPROVE,
            countersign_comments__isnull=False,
            countersigned_by__isnull=False,
        ).count() == len(case_subjects(case))

        assert QueuesEnum.FCDO_COUNTER_SIGNING not in [str(queue.id) for queue in case.queues.all()]
