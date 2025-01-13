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
from api.users.libraries.user_to_token import user_to_token
from api.users.tests.factories import GovUserFactory

from lite_routing.routing_rules_internal.enums import QueuesEnum, TeamIdEnum

pytestmark = pytest.mark.django_db


@pytest.fixture
def fcdo_bulk_approval_url():
    return reverse("caseworker_queues:bulk_approval", kwargs={"pk": QueuesEnum.FCDO})


@pytest.fixture
def mod_bulk_approval_url():
    return reverse("caseworker_queues:bulk_approval", kwargs={"pk": QueuesEnum.MOD_CAPPROT})


@pytest.fixture()
def team_case_advisor():
    def _team_case_advisor(team_id):
        gov_user = GovUserFactory()
        gov_user.team = Team.objects.get(id=team_id)
        gov_user.save()
        return gov_user

    return _team_case_advisor


@pytest.fixture()
def team_case_advisor_headers(team_case_advisor):
    def _team_case_advisor_headers(team_id):
        case_advisor = team_case_advisor(team_id)
        return {"HTTP_GOV_USER_TOKEN": user_to_token(case_advisor.baseuser_ptr)}

    return _team_case_advisor_headers


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

        cle = ControlListEntry.objects.get(rating="ML2a")
        gov_user = GovUserFactory()
        gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        gov_user.save()
        queue = Queue.objects.get(id=QueuesEnum.LU_PRE_CIRC)

        for application in applications:
            for good_on_application in application.goods.all():
                good_on_application.is_good_controlled = True
                good_on_application.save()
                good_on_application.control_list_entries.add(*[cle])
                good_on_application.good.control_list_entries.add(*[cle])

        for case in cases:
            case.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_REVIEW)
            case.save()
            case.queues.set([QueuesEnum.LU_PRE_CIRC])
            case.refresh_from_db()

            # Circulate to OGDs
            queue = Queue.objects.get(id=QueuesEnum.LU_PRE_CIRC)
            case.move_case_forward(queue, gov_user)

            # Reset queue with the specified OGD queue only
            case.refresh_from_db()
            target_queue = Queue.objects.get(id=queue_id)
            case.queues.set([target_queue])

        return cases

    return _get_cases_with_ogd_queue_assigned


def case_subjects(case):
    application = StandardApplication.objects.get(id=case.id)
    return list(application.goods.all()) + list(application.parties.all())


@pytest.mark.parametrize(
    "team_id, queue_id, next_queue_id",
    (
        (TeamIdEnum.MOD_CAPPROT, QueuesEnum.MOD_CAPPROT, QueuesEnum.MOD_ECJU_REVIEW_AND_COMBINE),
        (TeamIdEnum.MOD_DI, QueuesEnum.MOD_DI_DIRECT, QueuesEnum.LU_POST_CIRC),
        (TeamIdEnum.MOD_DI, QueuesEnum.MOD_DI_INDIRECT, QueuesEnum.MOD_ECJU_REVIEW_AND_COMBINE),
        (TeamIdEnum.MOD_DSR, QueuesEnum.MOD_DSR, QueuesEnum.MOD_ECJU_REVIEW_AND_COMBINE),
        (TeamIdEnum.MOD_DSTL, QueuesEnum.MOD_DSTL, QueuesEnum.MOD_ECJU_REVIEW_AND_COMBINE),
        (TeamIdEnum.NCSC, QueuesEnum.NCSC, QueuesEnum.LU_POST_CIRC),
    ),
)
def test_user_bulk_approves_cases(
    api_client,
    team_case_advisor_headers,
    get_cases_with_ogd_queue_assigned,
    team_id,
    queue_id,
    next_queue_id,
):
    cases = get_cases_with_ogd_queue_assigned(queue_id, count=25)
    data = {
        "cases": [str(case.id) for case in cases],
        "advice": {
            "text": "No concerns",
            "proviso": "",
            "note": "",
            "footnote_required": False,
            "footnote": "",
            "team": team_id,
        },
    }
    url = reverse("caseworker_queues:bulk_approval", kwargs={"pk": queue_id})
    headers = team_case_advisor_headers(team_id)
    response = api_client.post(url, data=data, **headers)
    assert response.status_code == 201

    for case in cases:
        case.refresh_from_db()
        assert case.advice.filter(
            level=AdviceLevel.USER,
            type=AdviceType.APPROVE,
            team_id=team_id,
        ).count() == len(case_subjects(case))

        assert queue_id not in [str(queue.id) for queue in case.queues.all()]
        assert next_queue_id in [str(queue.id) for queue in case.queues.all()]
        audit_event = Audit.objects.get(target_object_id=case.id, verb=AuditType.CREATE_BULK_APPROVAL_RECOMMENDATION)
        assert audit_event.payload == {
            "case_references": [case.reference_code for case in cases],
            "decision": AdviceType.APPROVE,
            "level": AdviceLevel.USER,
            "queue": Queue.objects.get(id=queue_id).name,
            "team_id": team_id,
            "count": len(cases),
        }


@pytest.mark.parametrize(
    "team_id, queue_id",
    (
        (TeamIdEnum.FCDO, QueuesEnum.FCDO),
        (TeamIdEnum.DESNZ_CHEMICAL, QueuesEnum.DESNZ_CHEMICAL),
        (TeamIdEnum.DESNZ_NUCLEAR, QueuesEnum.DESNZ_NUCLEAR),
        (TeamIdEnum.DESNZ_RUSSIA_SANCTIONS, QueuesEnum.DESNZ_RUSSIA_SANCTIONS),
        (TeamIdEnum.MOD_ECJU, QueuesEnum.MOD_ECJU_REVIEW_AND_COMBINE),
    ),
)
def test_user_bulk_approves_fails_for_unsupported_users(
    api_client, team_case_advisor_headers, get_cases_with_ogd_queue_assigned, team_id, queue_id
):
    cases = get_cases_with_ogd_queue_assigned(queue_id)
    data = {
        "case_ids": [str(case.id) for case in cases],
        "advice": {
            "text": "No concerns",
            "proviso": "",
            "note": "",
            "footnote_required": False,
            "footnote": "",
            "team": team_id,
        },
    }
    url = reverse("caseworker_queues:bulk_approval", kwargs={"pk": queue_id})
    headers = team_case_advisor_headers(team_id)
    response = api_client.post(url, data=data, **headers)
    assert response.status_code == 403

    for case in cases:
        assert (
            case.advice.filter(
                level=AdviceLevel.USER,
                type=AdviceType.APPROVE,
                team_id=team_id,
            ).count()
            == 0
        )

        assert queue_id in [str(queue.id) for queue in case.queues.all()]
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
