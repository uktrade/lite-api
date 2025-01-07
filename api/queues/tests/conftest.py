import pytest

from django.urls import reverse
from rest_framework.test import APIClient

from api.applications.tests.factories import DraftStandardApplicationFactory
from api.core.constants import ExporterPermissions, GovPermissions, Roles
from api.organisations.tests.factories import OrganisationFactory
from api.parties.tests.factories import PartyDocumentFactory
from api.teams.models import Team
from api.users.libraries.user_to_token import user_to_token
from api.users.models import BaseUser, Permission
from api.users.enums import SystemUser, UserType
from api.users.tests.factories import (
    BaseUserFactory,
    ExporterUserFactory,
    GovUserFactory,
    RoleFactory,
    UserOrganisationRelationshipFactory,
)

from lite_routing.routing_rules_internal.enums import TeamIdEnum

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def setup(gov_user):
    pass


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
    if BaseUser.objects.filter(id=SystemUser.id).exists():
        return BaseUser.objects.get(id=SystemUser.id)
    else:
        return BaseUserFactory(id=SystemUser.id)


@pytest.fixture()
def gov_headers(gov_user):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}


@pytest.fixture()
def gov_user():
    return GovUserFactory()


@pytest.fixture()
def lu_case_officer(gov_user_permissions):
    gov_user = GovUserFactory()
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
    gov_user.save()
    return gov_user


@pytest.fixture()
def mod_officer_headers(mod_officer):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(mod_officer.baseuser_ptr)}


@pytest.fixture()
def gov_user_permissions():
    for permission in GovPermissions:
        Permission.objects.get_or_create(id=permission.name, name=permission.value, type=UserType.INTERNAL.value)


@pytest.fixture()
def api_client():
    return APIClient()


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
        assert response.status_code == 200, response.json()["errors"]

        draft_application.refresh_from_db()
        return draft_application

    return _submit_application


@pytest.fixture
def standard_case(draft_standard_application, submit_application):
    return submit_application(draft_standard_application)
