import csv
import json
import pytest

from rest_framework import status

from api.cases.enums import CaseTypeEnum, CaseTypeSubTypeEnum
from api.cases.models import CaseType
from api.core.constants import GovPermissions
from api.letter_templates.models import LetterTemplate
from api.staticdata.letter_layouts.models import LetterLayout
from api.users.libraries.user_to_token import user_to_token
from api.users.enums import SystemUser, UserType
from api.users.models import BaseUser, Permission
from api.users.tests.factories import BaseUserFactory, GovUserFactory, RoleFactory


def load_json(filename):
    with open(filename) as f:
        return json.load(f)


@pytest.fixture()
def seed_layouts():
    layouts = load_json("api/data_workspace/v2/tests/bdd/initial_data/letter_layouts.json")
    for layout in layouts:
        LetterLayout.objects.get_or_create(**layout)


@pytest.fixture()
def seed_templates(seed_layouts):
    templates = load_json("api/data_workspace/v2/tests/bdd/initial_data/letter_templates.json")
    for template in templates:
        template_instance, _ = LetterTemplate.objects.get_or_create(**template)
        template_instance.case_types.add(CaseType.objects.get(id=CaseTypeEnum.SIEL.id))


@pytest.fixture()
def siel_template(seed_templates):
    return LetterTemplate.objects.get(layout_id="00000000-0000-0000-0000-000000000001")


@pytest.fixture(autouse=True)
def system_user(db):
    if BaseUser.objects.filter(id=SystemUser.id).exists():
        return BaseUser.objects.get(id=SystemUser.id)
    else:
        return BaseUserFactory(id=SystemUser.id)


@pytest.fixture()
def gov_user():
    return GovUserFactory()


@pytest.fixture()
def gov_user_permissions():
    for permission in GovPermissions:
        Permission.objects.get_or_create(id=permission.name, name=permission.name, type=UserType.INTERNAL)


@pytest.fixture()
def lu_case_officer(gov_user, gov_user_permissions):
    gov_user.role = RoleFactory(name="Case officer", type=UserType.INTERNAL)
    gov_user.role.permissions.set(
        [GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name, GovPermissions.MANAGE_LICENCE_DURATION.name]
    )
    gov_user.save()
    return gov_user


@pytest.fixture()
def gov_headers(gov_user):
    return {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}


@pytest.fixture()
def unpage_data(client):
    def _unpage_data(url):
        unpaged_results = []
        while True:
            response = client.get(url)
            assert response.status_code == status.HTTP_200_OK
            unpaged_results += response.data["results"]
            if not response.data["next"]:
                break
            url = response.data["next"]

        return unpaged_results

    return _unpage_data
