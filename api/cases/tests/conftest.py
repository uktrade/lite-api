import pytest

from django.urls import reverse
from rest_framework.test import APIClient

from api.applications.tests.factories import DraftStandardApplicationFactory
from api.core.constants import ExporterPermissions, GovPermissions
from api.organisations.tests.factories import OrganisationFactory
from api.parties.tests.factories import PartyDocumentFactory
from api.users.libraries.user_to_token import user_to_token
from api.users.models import Permission
from api.users.enums import UserType
from api.users.tests.factories import (
    ExporterUserFactory,
    GovUserFactory,
    RoleFactory,
    UserOrganisationRelationshipFactory,
)

pytestmark = pytest.mark.django_db


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


@pytest.fixture
def final_advice_url(standard_case):
    return reverse("cases:case_final_advice", kwargs={"pk": standard_case.pk})