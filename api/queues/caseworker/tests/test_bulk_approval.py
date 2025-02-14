import pytest

from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from api.applications.models import StandardApplication
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer
from api.cases.enums import AdviceLevel, AdviceType
from api.cases.models import Case, CaseAssignment, CaseQueueMovement
from api.cases.tests.factories import CaseAssignmentFactory
from api.core.constants import Roles
from api.queues.models import Queue
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.teams.models import Team
from api.users.enums import UserType
from api.users.libraries.user_to_token import user_to_token
from api.users.models import Role
from api.users.tests.factories import GovUserFactory, RoleFactory

from lite_routing.routing_rules_internal.enums import QueuesEnum, TeamIdEnum

pytestmark = pytest.mark.django_db

pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


@pytest.fixture()
def team_case_advisor():
    def _team_case_advisor(team_id):
        gov_user = GovUserFactory()
        if not Role.objects.filter(id=Roles.INTERNAL_DEFAULT_ROLE_ID, type=UserType.INTERNAL.value).exists():
            gov_user.role = RoleFactory(
                id=Roles.INTERNAL_DEFAULT_ROLE_ID, type=UserType.INTERNAL.value, name=Roles.INTERNAL_DEFAULT_ROLE_NAME
            )

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
def get_cases_with_ogd_queue_assigned(get_draft_application, submit_application, team_case_advisor):
    """Returns list of cases with the given OGD queue assigned"""

    def _get_cases_with_ogd_queue_assigned(queue_id, count=5):
        applications = [get_draft_application() for _ in range(count)]
        cases = [submit_application(application) for application in applications]

        cle = ControlListEntry.objects.get(rating="6A003b4c")
        for application in applications:
            for good_on_application in application.goods.all():
                good_on_application.is_good_controlled = True
                good_on_application.save()
                good_on_application.control_list_entries.add(*[cle])
                good_on_application.good.is_good_controlled = True
                good_on_application.good.control_list_entries.add(*[cle])

        for case in cases:
            case.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_REVIEW)
            case.save()

            # As part of the test here we are manually setting the queues hence we need
            # to create CaseQueueMovement instance as well as that gets updated when
            # this is moved forward in the next step
            case.queues.set([QueuesEnum.LU_PRE_CIRC])
            CaseQueueMovement.objects.create(case=case, queue_id=QueuesEnum.LU_PRE_CIRC)
            case.refresh_from_db()

            # Circulate to OGDs
            # When moved forward from Pre-circulation the OGDs it is going to be routed to depends on
            # the case attributes, however for the purpose of this test we want it to be routed to a
            # given OGD queue hence mock moving forward in this instance.
            with patch("api.workflow.user_queue_assignment.move_case_forward") as mock_move_case_forward:
                mock_move_case_forward.return_value = [queue_id]

                gov_user = team_case_advisor(TeamIdEnum.LICENSING_UNIT)
                queue = Queue.objects.get(id=QueuesEnum.LU_PRE_CIRC)
                case.move_case_forward(queue, gov_user)
                case.status = CaseStatus.objects.get(status=CaseStatusEnum.OGD_ADVICE)
                case.save()

            # We need this event to avoid triggering of fallback routing rule.
            # We are routing to a specific OGD queue_id for bulk approval.
            # After multiple cases are approved and moved forward then fallback rule gets triggered
            # as fallback rule doesn't consider bulk approval and routes to fallback OGD queues.
            # This makes it difficult to test the next queues after bulk approval. By creating this
            # event we ensure fallback is not triggered and we can determine the next queue as per
            # routing rules and assert the same in the tests
            #
            # In reality this won't be an issue as cases definitely gets routed to atleast one
            # other OGD
            obj = Audit.objects.create(
                actor=gov_user,
                verb=AuditType.MOVE_CASE,
                action_object=case,
                payload={
                    "queues": "FCDO Cases to Review",
                    "queue_ids": [QueuesEnum.FCDO],
                    "case_status": case.status.status,
                },
            )
            obj.action_object_content_type = ContentType.objects.get_for_model(Case)
            obj.save()

            # Reset queue with the specified OGD queue only because move case forward is mocked
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
    cases = get_cases_with_ogd_queue_assigned(queue_id, count=2)
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
        audit_text = AuditSerializer(audit_event).data["text"]
        assert audit_text == "added a recommendation using the Approve button in the queue."


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
    team_case_advisor,
    team_id,
    queue_id,
    next_queue_id,
):

    case = get_cases_with_ogd_queue_assigned(queue_id, count=1)[0]
    gov_user = team_case_advisor(team_id)
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
