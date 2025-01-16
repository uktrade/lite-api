import pytest

from django.urls import reverse
from urllib import parse

from api.applications.tests.factories import DraftStandardApplicationFactory
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer
from api.cases.enums import AdviceLevel, AdviceType
from api.cases.models import Case, CaseAssignment
from api.cases.tests.factories import CaseAssignmentFactory
from api.parties.tests.factories import PartyDocumentFactory
from api.queues.models import Queue
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.teams.models import Team
from api.users.enums import UserType
from api.users.libraries.user_to_token import user_to_token
from api.users.tests.factories import GovUserFactory

from lite_routing.routing_rules_internal.enums import QueuesEnum, TeamIdEnum

pytestmark = pytest.mark.django_db


@pytest.fixture
def activity_url():
    def _url(case):
        return reverse("cases:activity", kwargs={"pk": case.id})

    return _url


@pytest.fixture
def standard_case(organisation, submit_application):
    application = DraftStandardApplicationFactory(organisation=organisation)
    return submit_application(application)


@pytest.fixture
def standard_case_routed_to_ogds(organisation, submit_application, lu_case_officer):
    def _standard_case_routed_to_ogds():
        draft = DraftStandardApplicationFactory(organisation=organisation)
        application = submit_application(draft)
        cle = ControlListEntry.objects.get(rating="ML2a")
        queue = Queue.objects.get(id=QueuesEnum.LU_PRE_CIRC)

        for good_on_application in application.goods.all():
            good_on_application.is_good_controlled = True
            good_on_application.save()
            good_on_application.control_list_entries.add(*[cle])
            good_on_application.good.control_list_entries.add(*[cle])

        case = Case.objects.get(id=application.id)
        case.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_REVIEW)
        case.save()
        case.queues.set([QueuesEnum.LU_PRE_CIRC])
        case.refresh_from_db()

        # Circulate to OGDs
        queue = Queue.objects.get(id=QueuesEnum.LU_PRE_CIRC)
        case.move_case_forward(queue, lu_case_officer)

        return case

    return _standard_case_routed_to_ogds


def test_exporter_events(api_client, activity_url, standard_case, gov_headers):

    query_params = {"user_type": UserType.EXPORTER}
    url = f"{activity_url(standard_case)}?{parse.urlencode(query_params, doseq=True)}"

    response = api_client.get(url, **gov_headers)
    assert response.status_code == 200

    activities = response.json()["activity"]
    assert len(activities) == 1
    assert activities[0]["verb"] == "updated_status"
    assert activities[0]["text"] == "applied for a licence."


def test_caseworker_team_events(api_client, activity_url, standard_case_routed_to_ogds, lu_case_officer_headers):
    case = standard_case_routed_to_ogds()
    query_params = {"team_id": TeamIdEnum.LICENSING_UNIT}
    url = f"{activity_url(case)}?{parse.urlencode(query_params, doseq=True)}"

    response = api_client.get(url, **lu_case_officer_headers)
    assert response.status_code == 200

    activities = response.json()["activity"]
    assert len(activities) == 1
    assert activities[0]["verb"] == "unassigned_queues"
    assert (
        activities[0]["text"]
        == "marked themselves as done for this case on the following queues: Licensing Unit Pre-circulation Cases to Review."
    )
