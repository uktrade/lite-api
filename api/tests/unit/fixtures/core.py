import json
import pytest

from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient
from urllib import parse

from api.applications.tests.factories import DraftStandardApplicationFactory
from api.core.constants import ExporterPermissions, GovPermissions, Roles
from api.core.requests import get_hawk_sender
from api.organisations.tests.factories import OrganisationFactory
from api.parties.tests.factories import PartyDocumentFactory
from api.teams.models import Team
from api.users.libraries.user_to_token import user_to_token
from api.users.models import Permission, Role
from api.users.enums import UserType
from api.users.tests.factories import (
    ExporterUserFactory,
    GovUserFactory,
    RoleFactory,
    SystemUserFactory,
    UserOrganisationRelationshipFactory,
)

from lite_routing.routing_rules_internal.enums import TeamIdEnum

pytestmark = pytest.mark.django_db


class HawkClient(APIClient):
    def post(self, url, data, **kwargs):
        assert settings.HAWK_AUTHENTICATION_ENABLED  # nosec

        # Without this hawk sender gets data as string whereas
        # receiver gets it as bytes resulting in failure because
        # of hash mismatch. Our version on mohawk sender supports
        # receiving in bytes so convert before sending it.
        data = json.dumps(data).encode("utf-8")
        return super().post(url, data=data, content_type="application/json", **kwargs)


@pytest.fixture(autouse=True)
def django_db(db):
    return db


@pytest.fixture(autouse=True)
def setup(gov_user):
    pass


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture
def get_hawk_client():
    def _get_hawk_client(method, url, data=None):
        assert settings.HAWK_AUTHENTICATION_ENABLED  # nosec
        client = HawkClient()
        url = parse.urljoin("http://testserver", url)
        sender = get_hawk_sender(method, url, data, settings.HAWK_LITE_API_CREDENTIALS)
        client.credentials(HTTP_HAWK_AUTHENTICATION=sender.request_header, CONTENT_TYPE="application/json")
        return client, url

    return _get_hawk_client


@pytest.fixture()
def exporter_user():
    return ExporterUserFactory()


@pytest.fixture()
def exporter_user_permissions():
    for permission in ExporterPermissions:
        Permission.objects.get_or_create(id=permission.name, name=permission.value, type=UserType.EXPORTER.value)


@pytest.fixture()
def organisation(exporter_user_permissions, exporter_user):
    organisation = OrganisationFactory()

    UserOrganisationRelationshipFactory(
        organisation=organisation,
        role__permissions=[ExporterPermissions.SUBMIT_LICENCE_APPLICATION.name],
        user=exporter_user,
    )

    return organisation


@pytest.fixture()
def exporter_headers(exporter_user, organisation):
    return {
        "HTTP_EXPORTER_USER_TOKEN": user_to_token(exporter_user.baseuser_ptr),
        "HTTP_ORGANISATION_ID": str(organisation.id),
    }


@pytest.fixture(autouse=True)
def system_user():
    return SystemUserFactory()


@pytest.fixture()
def gov_headers(gov_user):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}


@pytest.fixture()
def gov_user():
    gov_user = GovUserFactory()
    if Role.objects.filter(id=Roles.INTERNAL_DEFAULT_ROLE_ID, type=UserType.INTERNAL.value).exists():
        return gov_user

    gov_user.role = RoleFactory(
        id=Roles.INTERNAL_DEFAULT_ROLE_ID, type=UserType.INTERNAL.value, name=Roles.INTERNAL_DEFAULT_ROLE_NAME
    )
    gov_user.save()

    return gov_user


@pytest.fixture()
def lu_case_officer(gov_user_permissions):
    gov_user = GovUserFactory()
    gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
    gov_user.role = RoleFactory(name="Case officer", type=UserType.INTERNAL)
    gov_user.role.permissions.set(
        [
            GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name,
            GovPermissions.MANAGE_LICENCE_DURATION.name,
            GovPermissions.REOPEN_CLOSED_CASES.name,
        ]
    )
    gov_user.save()
    return gov_user


@pytest.fixture()
def lu_case_officer_headers(lu_case_officer):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(lu_case_officer.baseuser_ptr)}


@pytest.fixture()
def fcdo_officer():
    gov_user = GovUserFactory()
    gov_user.team = Team.objects.get(name="FCDO")
    gov_user.save()
    return gov_user


@pytest.fixture()
def fcdo_officer_headers(fcdo_officer):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(fcdo_officer.baseuser_ptr)}


@pytest.fixture()
def fcdo_countersigner(gov_user_permissions):
    gov_user = GovUserFactory()
    gov_user.team = Team.objects.get(name="FCDO")
    gov_user.role = RoleFactory(name="FCDO Countersigner", type=UserType.INTERNAL)
    gov_user.role.permissions.set(
        [
            GovPermissions.MANAGE_TEAM_ADVICE.name,
        ]
    )
    gov_user.save()
    return gov_user


@pytest.fixture()
def fcdo_countersigner_headers(fcdo_countersigner):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(fcdo_countersigner.baseuser_ptr)}


@pytest.fixture()
def mod_officer():
    gov_user = GovUserFactory()
    gov_user.team = Team.objects.get(id=TeamIdEnum.MOD_CAPPROT)
    gov_user.role = RoleFactory(name="MOD CapProt officer", type=UserType.INTERNAL)
    gov_user.save()
    return gov_user


@pytest.fixture()
def mod_officer_headers(mod_officer):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(mod_officer.baseuser_ptr)}


@pytest.fixture()
def gov_user_permissions():
    for permission in GovPermissions:
        Permission.objects.get_or_create(id=permission.name, name=permission.value, type=UserType.INTERNAL.value)


@pytest.fixture
def draft_standard_application(organisation):
    application = DraftStandardApplicationFactory(organisation=organisation)
    PartyDocumentFactory(
        party=application.end_user.party,
        s3_key="end-user-undertaking",
        safe=True,
    )
    return application


@pytest.fixture
def get_draft_application(organisation):

    def _get_draft_application():
        return DraftStandardApplicationFactory(organisation=organisation)

    return _get_draft_application


@pytest.fixture
def submit_application(api_client, exporter_headers, mocker):
    def _submit_application(draft_application):
        mocker.patch("api.documents.libraries.s3_operations.upload_bytes_file", return_value=None)
        response = api_client.put(
            reverse(
                "applications:application_submit",
                kwargs={
                    "pk": draft_application.pk,
                },
            ),
            data={
                "submit_declaration": True,
                "agreed_to_declaration_text": "i agree",
            },
            **exporter_headers,
        )
        assert response.status_code == 200, response.json()["errors"]  # nosec

        draft_application.refresh_from_db()
        return draft_application

    return _submit_application


@pytest.fixture
def standard_case(draft_standard_application, submit_application):
    return submit_application(draft_standard_application)


@pytest.fixture
def final_advice_url(standard_case):
    return reverse("cases:case_final_advice", kwargs={"pk": standard_case.pk})


@pytest.fixture()
def team_case_advisor():
    def _team_case_advisor(team_id, permissions=None):
        gov_user = GovUserFactory()
        if not Role.objects.filter(id=Roles.INTERNAL_DEFAULT_ROLE_ID, type=UserType.INTERNAL.value).exists():
            gov_user.role = RoleFactory(
                id=Roles.INTERNAL_DEFAULT_ROLE_ID, type=UserType.INTERNAL.value, name=Roles.INTERNAL_DEFAULT_ROLE_NAME
            )

        gov_user.team = Team.objects.get(id=team_id)
        if permissions and isinstance(permissions, list):
            gov_user.role.permissions.set(permissions)

        gov_user.save()
        return gov_user

    return _team_case_advisor


@pytest.fixture()
def team_case_advisor_headers(team_case_advisor):
    def _team_case_advisor_headers(team_id):
        case_advisor = team_case_advisor(team_id)
        return {"HTTP_GOV_USER_TOKEN": user_to_token(case_advisor.baseuser_ptr)}

    return _team_case_advisor_headers
