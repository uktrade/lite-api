import pytest

from django.urls import reverse

from api.applications.models import StandardApplication
from api.applications.tests.factories import DraftStandardApplicationFactory
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import AdviceLevel, AdviceType
from api.parties.tests.factories import PartyDocumentFactory
from api.queues.models import Queue
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus

from lite_routing.routing_rules_internal.enums import QueuesEnum, TeamIdEnum

pytestmark = pytest.mark.django_db


@pytest.fixture
def fcdo_bulk_approval_url():
    return reverse("caseworker_queues:bulk_approval", kwargs={"pk": QueuesEnum.FCDO})


@pytest.fixture
def mod_bulk_approval_url():
    return reverse("caseworker_queues:bulk_approval", kwargs={"pk": QueuesEnum.MOD_CAPPROT})


@pytest.fixture
def multiple_cases_ogd_queue(organisation, submit_application):

    def _multiple_cases_ogd_queue(queue_id, count=5):
        ogd_advice = CaseStatus.objects.get(status=CaseStatusEnum.OGD_ADVICE)
        draft_applications = [DraftStandardApplicationFactory(organisation=organisation) for i in range(count)]
        _ = [
            PartyDocumentFactory(
                party=application.end_user.party,
                s3_key="party-document",
                safe=True,
            )
            for application in draft_applications
        ]
        cases = [submit_application(application) for application in draft_applications]
        for case in cases:
            case.status = ogd_advice
            case.save()
            case.queues.add(*[queue_id])

        return cases

    return _multiple_cases_ogd_queue


def case_subjects(case):
    application = StandardApplication.objects.get(id=case.id)
    return list(application.goods.all()) + list(application.parties.all())


def test_user_bulk_approves_cases(api_client, mod_officer_headers, mod_bulk_approval_url, multiple_cases_ogd_queue):
    cases = multiple_cases_ogd_queue(QueuesEnum.MOD_CAPPROT, count=25)
    data = {
        "case_ids": [str(case.id) for case in cases],
        "advice": {
            "text": "No concerns",
            "proviso": "",
            "note": "",
            "footnote_required": False,
            "footnote": "",
            "team": TeamIdEnum.MOD_CAPPROT,
        },
    }
    response = api_client.post(mod_bulk_approval_url, data=data, **mod_officer_headers)
    assert response.status_code == 201

    for case in cases:
        assert case.advice.filter(
            level=AdviceLevel.USER,
            type=AdviceType.APPROVE,
            team_id=TeamIdEnum.MOD_CAPPROT,
        ).count() == len(case_subjects(case))

        assert QueuesEnum.MOD_CAPPROT not in [str(queue.id) for queue in case.queues.all()]
        assert QueuesEnum.MOD_ECJU_REVIEW_AND_COMBINE in [str(queue.id) for queue in case.queues.all()]
        audit_event = Audit.objects.get(target_object_id=case.id, verb=AuditType.CREATE_BULK_APPROVAL_RECOMMENDATION)
        assert audit_event.payload == {
            "case_references": [case.reference_code for case in cases],
            "decision": AdviceType.APPROVE,
            "level": AdviceLevel.USER,
            "queue": Queue.objects.get(id=QueuesEnum.MOD_CAPPROT).name,
            "team_id": TeamIdEnum.MOD_CAPPROT,
            "count": len(cases),
        }


def test_user_bulk_approves_fails_for_unsupported_users(
    api_client, fcdo_officer_headers, fcdo_bulk_approval_url, multiple_cases_ogd_queue
):
    cases = multiple_cases_ogd_queue(QueuesEnum.FCDO)
    data = {
        "case_ids": [str(case.id) for case in cases],
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
    assert response.status_code == 403

    for case in cases:
        assert (
            case.advice.filter(
                level=AdviceLevel.USER,
                type=AdviceType.APPROVE,
                team_id=TeamIdEnum.FCDO,
            ).count()
            == 0
        )

        assert QueuesEnum.FCDO in [str(queue.id) for queue in case.queues.all()]
        assert (
            Audit.objects.filter(target_object_id=case.id, verb=AuditType.CREATE_BULK_APPROVAL_RECOMMENDATION).exists()
            is False
        )
