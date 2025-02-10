import pytest

from django.urls import reverse
from freezegun import freeze_time
from unittest.mock import patch

from api.cases.models import CaseQueueMovement
from api.core.constants import Roles
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.countries.models import Country
from api.staticdata.report_summaries.models import ReportSummary, ReportSummarySubject
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.teams.models import Team
from api.users.enums import UserType
from api.users.libraries.user_to_token import user_to_token
from api.users.models import Role
from api.users.tests.factories import GovUserFactory, RoleFactory

from lite_routing.routing_rules_internal.enums import QueuesEnum, TeamIdEnum

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
def get_standard_case(get_draft_application, submit_application):

    def _get_standard_case(country_code):
        application = get_draft_application()
        for party_on_application in application.parties.all():
            party_on_application.party.country = Country.objects.get(id=country_code)
            party_on_application.party.save()

        case = submit_application(application)

        # Regimes are required to ensure it gets countersigning flags
        cle = ControlListEntry.objects.get(rating="6A003b4c")
        subject = ReportSummarySubject.objects.get(name="imaging cameras")
        rs = ReportSummary.objects.get(prefix=None, subject=subject)
        regime = RegimeEntry.objects.get(shortened_name="WS")
        for good_on_application in application.goods.all():
            good_on_application.is_good_controlled = True
            good_on_application.save()
            good_on_application.control_list_entries.add(*[cle])
            good_on_application.report_summaries.add(*[rs])
            good_on_application.regime_entries.add(*[regime])
            good_on_application.good.is_good_controlled = True
            good_on_application.good.control_list_entries.add(*[cle])

        return case

    return _get_standard_case


@pytest.mark.parametrize(
    "data",
    (
        [
            (
                # Instead of freezing time for whole test it is modified for each iteration because
                # the fallback routing rule incorrectly determining that it didn't go through OGD queues
                # when all the instances have same time
                "2025-01-10T12:00:00+00:00",
                CaseStatusEnum.SUBMITTED,
                TeamIdEnum.LICENSING_RECEPTION,
                QueuesEnum.LICENSING_RECEPTION_SIEL_APPLICATIONS,
                CaseStatusEnum.INITIAL_CHECKS,
                [QueuesEnum.TECHNICAL_ASSESSMENT_UNIT_SIELS_TO_REVIEW, QueuesEnum.ENFORCEMENT_UNIT_CASES_TO_REVIEW],
            ),
            (
                "2025-01-11T12:00:00+00:00",
                CaseStatusEnum.INITIAL_CHECKS,
                TeamIdEnum.TECHNICAL_ASSESSMENT_UNIT,
                QueuesEnum.TECHNICAL_ASSESSMENT_UNIT_SIELS_TO_REVIEW,
                CaseStatusEnum.INITIAL_CHECKS,
                [QueuesEnum.ENFORCEMENT_UNIT_CASES_TO_REVIEW],
            ),
            (
                "2025-01-12T12:00:00+00:00",
                CaseStatusEnum.INITIAL_CHECKS,
                TeamIdEnum.ENFORCEMENT_UNIT,
                QueuesEnum.ENFORCEMENT_UNIT_CASES_TO_REVIEW,
                CaseStatusEnum.UNDER_REVIEW,
                [QueuesEnum.LU_PRE_CIRC],
            ),
            (
                "2025-01-13T12:00:00+00:00",
                CaseStatusEnum.UNDER_REVIEW,
                TeamIdEnum.LICENSING_UNIT,
                QueuesEnum.LU_PRE_CIRC,
                CaseStatusEnum.OGD_ADVICE,
                [QueuesEnum.FCDO, QueuesEnum.MOD_DI_DIRECT],
            ),
            (
                "2025-01-14T12:00:00+00:00",
                CaseStatusEnum.OGD_ADVICE,
                TeamIdEnum.FCDO,
                QueuesEnum.FCDO,
                CaseStatusEnum.OGD_ADVICE,
                [QueuesEnum.FCDO_COUNTER_SIGNING],
            ),
            (
                "2025-01-15T12:00:00+00:00",
                CaseStatusEnum.OGD_ADVICE,
                TeamIdEnum.FCDO,
                QueuesEnum.FCDO_COUNTER_SIGNING,
                CaseStatusEnum.OGD_ADVICE,
                [QueuesEnum.MOD_DI_DIRECT],
            ),
            (
                "2025-01-16T12:00:00+00:00",
                CaseStatusEnum.OGD_ADVICE,
                TeamIdEnum.MOD_DI,
                QueuesEnum.MOD_DI_DIRECT,
                CaseStatusEnum.UNDER_FINAL_REVIEW,
                [QueuesEnum.LU_POST_CIRC],
            ),
        ],
    ),
)
def test_case_queue_movements(
    api_client,
    team_case_advisor_headers,
    get_standard_case,
    data,
):
    freezer = freeze_time("2025-01-10T12:00:00+00:00")
    freezer.start()
    case = get_standard_case("KR")
    freezer.stop()

    # This is processed in a loop instead of using parametrize because we want to retain
    # CaseQueueMovement instances for assertions. With parametrize they get cleared
    # during teardown at the end of each iteration
    for action_time, case_status, team_id, current_queue, next_status, expected_queues in data:
        case.status = CaseStatus.objects.get(status=case_status)
        case.save()
        case.refresh_from_db()

        with freeze_time(action_time):
            url = reverse("cases:assigned_queues", kwargs={"pk": case.id})
            headers = team_case_advisor_headers(team_id)
            response = api_client.put(url, data={"queues": [current_queue]}, **headers)
            assert response.status_code == 200

            case.refresh_from_db()
            assert case.status.status == next_status

        # check queue movement instances are created and recorded correctly
        obj = CaseQueueMovement.objects.get(case=case, queue=current_queue)
        assert obj.exit_date.isoformat() == action_time

        for queue in expected_queues:
            assert CaseQueueMovement.objects.get(case=case, queue=queue, exit_date=None)


@patch(
    "lite_routing.routing_rules_internal.routing_rules_criteria.is_all_countersign_advice_approved_by_licensing_manager"
)
@pytest.mark.parametrize(
    "data",
    (
        [
            (
                "2025-01-10T12:00:00+00:00",
                CaseStatusEnum.SUBMITTED,
                TeamIdEnum.LICENSING_RECEPTION,
                QueuesEnum.LICENSING_RECEPTION_SIEL_APPLICATIONS,
                CaseStatusEnum.INITIAL_CHECKS,
                [QueuesEnum.TECHNICAL_ASSESSMENT_UNIT_SIELS_TO_REVIEW, QueuesEnum.ENFORCEMENT_UNIT_CASES_TO_REVIEW],
            ),
            (
                "2025-01-11T12:00:00+00:00",
                CaseStatusEnum.INITIAL_CHECKS,
                TeamIdEnum.TECHNICAL_ASSESSMENT_UNIT,
                QueuesEnum.TECHNICAL_ASSESSMENT_UNIT_SIELS_TO_REVIEW,
                CaseStatusEnum.INITIAL_CHECKS,
                [QueuesEnum.ENFORCEMENT_UNIT_CASES_TO_REVIEW],
            ),
            (
                "2025-01-12T12:00:00+00:00",
                CaseStatusEnum.INITIAL_CHECKS,
                TeamIdEnum.ENFORCEMENT_UNIT,
                QueuesEnum.ENFORCEMENT_UNIT_CASES_TO_REVIEW,
                CaseStatusEnum.UNDER_REVIEW,
                [QueuesEnum.LU_PRE_CIRC],
            ),
            (
                "2025-01-13T12:00:00+00:00",
                CaseStatusEnum.UNDER_REVIEW,
                TeamIdEnum.LICENSING_UNIT,
                QueuesEnum.LU_PRE_CIRC,
                CaseStatusEnum.OGD_ADVICE,
                [QueuesEnum.FCDO, QueuesEnum.MOD_DI_DIRECT],
            ),
            (
                "2025-01-14T12:00:00+00:00",
                CaseStatusEnum.OGD_ADVICE,
                TeamIdEnum.FCDO,
                QueuesEnum.FCDO,
                CaseStatusEnum.OGD_ADVICE,
                [QueuesEnum.FCDO_COUNTER_SIGNING],
            ),
            (
                "2025-01-15T12:00:00+00:00",
                CaseStatusEnum.OGD_ADVICE,
                TeamIdEnum.FCDO,
                QueuesEnum.FCDO_COUNTER_SIGNING,
                CaseStatusEnum.OGD_ADVICE,
                [QueuesEnum.MOD_DI_DIRECT],
            ),
            (
                "2025-01-16T12:00:00+00:00",
                CaseStatusEnum.OGD_ADVICE,
                TeamIdEnum.MOD_DI,
                QueuesEnum.MOD_DI_DIRECT,
                CaseStatusEnum.UNDER_FINAL_REVIEW,
                [QueuesEnum.LU_POST_CIRC],
            ),
            (
                "2025-01-17T12:00:00+00:00",
                CaseStatusEnum.UNDER_FINAL_REVIEW,
                TeamIdEnum.LICENSING_UNIT,
                QueuesEnum.LU_POST_CIRC,
                CaseStatusEnum.FINAL_REVIEW_COUNTERSIGN,
                [QueuesEnum.LU_COUNTERSIGN],
            ),
            (
                "2025-01-18T12:00:00+00:00",
                CaseStatusEnum.FINAL_REVIEW_COUNTERSIGN,
                TeamIdEnum.LICENSING_UNIT,
                QueuesEnum.LU_COUNTERSIGN,
                CaseStatusEnum.FINAL_REVIEW_SECOND_COUNTERSIGN,
                [QueuesEnum.LU_SECOND_COUNTERSIGN],
            ),
            (
                "2025-01-19T12:00:00+00:00",
                CaseStatusEnum.FINAL_REVIEW_SECOND_COUNTERSIGN,
                TeamIdEnum.LICENSING_UNIT,
                QueuesEnum.LU_SECOND_COUNTERSIGN,
                CaseStatusEnum.UNDER_FINAL_REVIEW,
                [QueuesEnum.LU_POST_CIRC],
            ),
        ],
    ),
)
def test_case_queue_movements_with_lu_countersigning(
    mock_lm_countersign_approved,
    api_client,
    team_case_advisor_headers,
    get_standard_case,
    data,
):
    # this is mocked to avoid creating final advice and corresponding countersignatures
    mock_lm_countersign_approved.return_value = True

    freezer = freeze_time("2025-01-10T12:00:00+00:00")
    freezer.start()
    case = get_standard_case("HK")
    freezer.stop()

    for action_time, case_status, team_id, current_queue, next_status, expected_queues in data:
        case.status = CaseStatus.objects.get(status=case_status)
        case.save()
        case.refresh_from_db()

        with freeze_time(action_time):
            url = reverse("cases:assigned_queues", kwargs={"pk": case.id})
            headers = team_case_advisor_headers(team_id)
            response = api_client.put(url, data={"queues": [current_queue]}, **headers)
            assert response.status_code == 200

            case.refresh_from_db()
            assert case.status.status == next_status

        # check queue movement instances are created and recorded correctly
        obj = CaseQueueMovement.objects.get(case=case, queue=current_queue)
        assert obj.exit_date.isoformat() == action_time

        for queue in expected_queues:
            assert CaseQueueMovement.objects.get(case=case, queue=queue, exit_date=None)


@pytest.mark.parametrize(
    "data",
    (
        [
            (
                # Instead of freezing time for whole test it is modified for each iteration because
                # the fallback routing rule incorrectly determining that it didn't go through OGD queues
                # when all the instances have same time
                "2025-01-10T12:00:00+00:00",
                CaseStatusEnum.SUBMITTED,
                TeamIdEnum.LICENSING_RECEPTION,
                QueuesEnum.LICENSING_RECEPTION_SIEL_APPLICATIONS,
                CaseStatusEnum.INITIAL_CHECKS,
                [QueuesEnum.TECHNICAL_ASSESSMENT_UNIT_SIELS_TO_REVIEW, QueuesEnum.ENFORCEMENT_UNIT_CASES_TO_REVIEW],
            ),
            (
                "2025-01-11T12:00:00+00:00",
                CaseStatusEnum.INITIAL_CHECKS,
                TeamIdEnum.ENFORCEMENT_UNIT,
                QueuesEnum.ENFORCEMENT_UNIT_CASES_TO_REVIEW,
                CaseStatusEnum.INITIAL_CHECKS,
                [QueuesEnum.TECHNICAL_ASSESSMENT_UNIT_SIELS_TO_REVIEW],
            ),
            (
                "2025-01-12T12:00:00+00:00",
                CaseStatusEnum.INITIAL_CHECKS,
                TeamIdEnum.TECHNICAL_ASSESSMENT_UNIT,
                QueuesEnum.TECHNICAL_ASSESSMENT_UNIT_SIELS_TO_REVIEW,
                CaseStatusEnum.UNDER_REVIEW,
                [QueuesEnum.LU_PRE_CIRC],
            ),
            (
                "2025-01-13T12:00:00+00:00",
                CaseStatusEnum.UNDER_REVIEW,
                TeamIdEnum.LICENSING_UNIT,
                QueuesEnum.LU_PRE_CIRC,
                CaseStatusEnum.OGD_ADVICE,
                [QueuesEnum.FCDO, QueuesEnum.MOD_DI_DIRECT],
            ),
            (
                "2025-01-14T12:00:00+00:00",
                CaseStatusEnum.OGD_ADVICE,
                TeamIdEnum.FCDO,
                QueuesEnum.FCDO,
                CaseStatusEnum.OGD_ADVICE,
                [QueuesEnum.FCDO_COUNTER_SIGNING],
            ),
            (
                "2025-01-15T12:00:00+00:00",
                CaseStatusEnum.OGD_ADVICE,
                TeamIdEnum.FCDO,
                QueuesEnum.FCDO_COUNTER_SIGNING,
                CaseStatusEnum.OGD_ADVICE,
                [QueuesEnum.MOD_DI_DIRECT],
            ),
            (
                "2025-01-16T12:00:00+00:00",
                CaseStatusEnum.OGD_ADVICE,
                TeamIdEnum.MOD_DI,
                QueuesEnum.MOD_DI_DIRECT,
                CaseStatusEnum.UNDER_FINAL_REVIEW,
                [QueuesEnum.LU_POST_CIRC],
            ),
        ],
    ),
)
def test_case_queue_movements_when_case_sent_back_to_tau(
    api_client,
    team_case_advisor_headers,
    get_standard_case,
    data,
):
    freezer = freeze_time("2025-01-10T12:00:00+00:00")
    freezer.start()
    case = get_standard_case("KR")
    freezer.stop()

    # This is processed in a loop instead of using parametrize because we want to retain
    # CaseQueueMovement instances for assertions. With parametrize they get cleared
    # during teardown at the end of each iteration
    for action_date, case_status, team_id, current_queue, next_status, expected_queues in data:
        case.status = CaseStatus.objects.get(status=case_status)
        case.save()
        case.refresh_from_db()

        with freeze_time(action_date):
            url = reverse("cases:assigned_queues", kwargs={"pk": case.id})
            headers = team_case_advisor_headers(team_id)
            response = api_client.put(url, data={"queues": [current_queue]}, **headers)
            assert response.status_code == 200

            case.refresh_from_db()
            assert case.status.status == next_status

        # check queue movement instances are created and recorded correctly
        obj = CaseQueueMovement.objects.get(case=case, queue=current_queue)
        assert obj.exit_date.isoformat() == action_date

        for queue in expected_queues:
            assert CaseQueueMovement.objects.get(case=case, queue=queue, exit_date=None)

    # Now we send the case back to TAU
    with freeze_time("2025-01-20T12:00:00+00:00"):
        url = reverse("caseworker_applications:change_status", kwargs={"pk": str(case.id)})
        headers = team_case_advisor_headers(TeamIdEnum.LICENSING_UNIT)
        response = api_client.post(url, data={"status": CaseStatusEnum.INITIAL_CHECKS}, **headers)
        assert response.status_code == 200
        case.refresh_from_db()

    assert case.status == CaseStatus.objects.get(status=CaseStatusEnum.INITIAL_CHECKS)
    assert [str(item) for item in case.queues.values_list("id", flat=True)] == [
        QueuesEnum.ENFORCEMENT_UNIT_CASES_TO_REVIEW,
        QueuesEnum.TECHNICAL_ASSESSMENT_UNIT_SIELS_TO_REVIEW,
    ]

    # Assume TAU have made few changes
    # The same flow repeats but from Enforcement unit and TAU stage in the 'data'
    return_date = 20
    for _, case_status, team_id, current_queue, next_status, expected_queues in data[1:]:
        case.status = CaseStatus.objects.get(status=case_status)
        case.save()
        case.refresh_from_db()

        action_date = f"2025-01-{return_date}T12:00:00+00:00"
        return_date += 1

        with freeze_time(action_date):
            url = reverse("cases:assigned_queues", kwargs={"pk": case.id})
            headers = team_case_advisor_headers(team_id)
            response = api_client.put(url, data={"queues": [current_queue]}, **headers)
            assert response.status_code == 200

            case.refresh_from_db()
            assert case.status.status == next_status

        # check queue movement instances are created and recorded correctly
        obj = CaseQueueMovement.objects.filter(case=case, queue=current_queue).order_by("exit_date").last()
        assert obj.exit_date.isoformat() == action_date

        for queue in expected_queues:
            assert CaseQueueMovement.objects.get(case=case, queue=queue, exit_date=None)
