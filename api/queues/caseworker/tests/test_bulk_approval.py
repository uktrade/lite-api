import pytest

from django.urls import reverse

from api.applications.models import StandardApplication
from api.applications.tests.factories import DraftStandardApplicationFactory
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import AdviceLevel, AdviceType
from api.cases.models import CaseAssignment
from api.cases.tests.factories import CaseAssignmentFactory
from api.parties.tests.factories import PartyDocumentFactory
from api.queues.models import Queue
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.teams.models import Team
from api.users.tests.factories import GovUserFactory

from lite_routing.routing_rules_internal.enums import QueuesEnum, TeamIdEnum

pytestmark = pytest.mark.django_db


@pytest.fixture
def fcdo_bulk_approval_url():
    return reverse("caseworker_queues:bulk_approval", kwargs={"pk": QueuesEnum.FCDO})


@pytest.fixture
def mod_bulk_approval_url():
    return reverse("caseworker_queues:bulk_approval", kwargs={"pk": QueuesEnum.MOD_CAPPROT})


@pytest.fixture
def get_cases_with_ogd_queue_assigned(organisation, submit_application):

    def _get_cases_with_ogd_queue_assigned(queue_id, count=5):
        applications = [DraftStandardApplicationFactory(organisation=organisation) for i in range(count)]
        _ = [
            PartyDocumentFactory(
                party=application.end_user.party,
                s3_key="party-document",
                safe=True,
            )
            for application in applications
        ]
        cases = [submit_application(application) for application in applications]

        cle = ControlListEntry.objects.get(rating="PL9002b")
        gov_user = GovUserFactory()
        gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        gov_user.save()
        queue = Queue.objects.get(id=QueuesEnum.LU_PRE_CIRC)

        for application in applications:
            for good_on_application in application.goods.all():
                good_on_application.is_good_controlled = True
                good_on_application.control_list_entries.add(*[cle])
                good_on_application.good.control_list_entries.add(*[cle])

        for case in cases:
            case.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_REVIEW)
            case.save()
            case.queues.set([QueuesEnum.LU_PRE_CIRC])
            case.refresh_from_db()

            # Circulate to OGDs
            case.move_case_forward(queue, gov_user)

            # Reset queue with the specified OGD queue only
            queue = Queue.objects.get(id=queue_id)
            case.refresh_from_db()
            case.queues.set([queue])

        return cases

    return _get_cases_with_ogd_queue_assigned


def case_subjects(case):
    application = StandardApplication.objects.get(id=case.id)
    return list(application.goods.all()) + list(application.parties.all())


def test_user_bulk_approves_cases(
    api_client, mod_officer_headers, mod_bulk_approval_url, get_cases_with_ogd_queue_assigned
):
    cases = get_cases_with_ogd_queue_assigned(QueuesEnum.MOD_CAPPROT, count=25)
    data = {
        "cases": [str(case.id) for case in cases],
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
    api_client, fcdo_officer_headers, fcdo_bulk_approval_url, get_cases_with_ogd_queue_assigned
):
    cases = get_cases_with_ogd_queue_assigned(QueuesEnum.FCDO)
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


@pytest.mark.parametrize(
    "team_id, queue_id,next_queue_id",
    (
        (TeamIdEnum.DESNZ_CHEMICAL, QueuesEnum.DESNZ_CHEMICAL, QueuesEnum.LU_POST_CIRC),
        (TeamIdEnum.DESNZ_NUCLEAR, QueuesEnum.DESNZ_NUCLEAR, QueuesEnum.DESNZ_NUCLEAR_COUNTERSIGNING),
        (TeamIdEnum.FCDO, QueuesEnum.FCDO, QueuesEnum.FCDO_COUNTER_SIGNING),
        (TeamIdEnum.FCDO, QueuesEnum.FCDO_COUNTER_SIGNING, QueuesEnum.LU_POST_CIRC),
        (TeamIdEnum.MOD_CAPPROT, QueuesEnum.MOD_CAPPROT, QueuesEnum.MOD_ECJU_REVIEW_AND_COMBINE),
        (TeamIdEnum.MOD_DI, QueuesEnum.MOD_DI_DIRECT, QueuesEnum.LU_POST_CIRC),
        (TeamIdEnum.MOD_DI, QueuesEnum.MOD_DI_INDIRECT, QueuesEnum.MOD_ECJU_REVIEW_AND_COMBINE),
        (TeamIdEnum.MOD_DSR, QueuesEnum.MOD_DSR, QueuesEnum.MOD_ECJU_REVIEW_AND_COMBINE),
        (TeamIdEnum.MOD_DSTL, QueuesEnum.MOD_DSTL, QueuesEnum.MOD_ECJU_REVIEW_AND_COMBINE),
        (TeamIdEnum.NCSC, QueuesEnum.NCSC, QueuesEnum.LU_POST_CIRC),
    ),
)
def test_case_move_forward(
    get_cases_with_ogd_queue_assigned,
    team_id,
    queue_id,
    next_queue_id,
):

    case = get_cases_with_ogd_queue_assigned(queue_id, count=1)[0]
    gov_user = GovUserFactory()
    gov_user.team = Team.objects.get(id=team_id)
    gov_user.save()

    queue = Queue.objects.get(id=queue_id)
    CaseAssignmentFactory(case=case, queue=queue, user=gov_user)

    case.move_case_forward(queue, gov_user)

    assert CaseAssignment.objects.filter(case=case, queue=queue, user=gov_user).exists() is False
    assert queue_id not in [str(queue.id) for queue in case.queues.all()]
    assert next_queue_id in [str(queue.id) for queue in case.queues.all()]
    audit_event = Audit.objects.filter(target_object_id=case.id, verb=AuditType.UNASSIGNED_QUEUES).first()
    assert audit_event.payload == {
        "queues": [queue.name],
    }
