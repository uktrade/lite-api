import json
import os
import pytest

from parameterized import parameterized
from tempfile import NamedTemporaryFile

from api.cases.enums import CaseTypeEnum
from api.cases.models import CaseType
from api.core.constants import GovPermissions, ExporterPermissions, Teams
from api.conf.settings import BASE_DIR
from api.letter_templates.models import LetterTemplate
from api.staticdata.countries.models import Country
from api.cases.enums import AdviceType
from api.queues.constants import ALL_CASES_QUEUE_ID
from api.staticdata.decisions.models import Decision
from api.staticdata.denial_reasons.models import DenialReason
from api.staticdata.letter_layouts.models import LetterLayout
from api.staticdata.management.SeedCommand import SeedCommandTest
from api.staticdata.management.commands import (
    seedlayouts,
    seedcasestatuses,
    seedcasetypes,
    seedcountries,
    seeddenialreasons,
    seedlettertemplates,
    seedrolepermissions,
    seedfinaldecisions,
    seedinternalusers,
)
from api.staticdata.statuses.models import CaseStatus, CaseStatusCaseType
from api.teams.enums import TeamIdEnum
from api.users.enums import UserType
from api.users.models import GovUser, Permission
from api.users.tests.factories import RoleFactory


class SeedingTests(SeedCommandTest):
    def setUp(self) -> None:
        super().setUp()
        role_names = ["Super User", "Case officer", "Case adviser", "Manager", "Senior Manager"]
        for name in role_names:
            RoleFactory(name=name, type=UserType.INTERNAL)

    @pytest.mark.seeding
    def test_seed_case_types(self):
        self.seed_command(seedcasetypes.Command)
        enum = CaseTypeEnum.CASE_TYPE_LIST
        self.assertEqual(CaseType.objects.count(), len(enum))
        for item in enum:
            self.assertTrue(CaseType.objects.get(id=item.id))

    @pytest.mark.seeding
    def test_seed_case_statuses(self):
        self.seed_command(seedcasetypes.Command)
        self.seed_command(seedcasestatuses.Command, "--force")
        self.assertTrue(
            CaseStatus.objects.count() >= len(seedcasestatuses.Command.read_csv(seedcasestatuses.STATUSES_FILE))
        )

        case_type_list = CaseTypeEnum.CASE_TYPE_LIST
        counter = 0
        for case_type in case_type_list:
            for key, value in seedcasestatuses.Command.STATUSES_ON_CASE_TYPES.items():
                if case_type.sub_type in value or case_type.type in value:
                    counter += 1

        self.assertEqual(CaseStatusCaseType.objects.all().count(), counter)

    @pytest.mark.seeding
    def test_seed_countries(self):
        self.seed_command(seedcountries.Command)
        self.assertEqual(Country.objects.count(), len(seedcountries.Command.read_csv(seedcountries.COUNTRIES_FILE)))

    @pytest.mark.seeding
    def test_seed_denial_reasons(self):
        self.seed_command(seeddenialreasons.Command)
        self.assertEqual(
            DenialReason.objects.count(), len(seeddenialreasons.Command.read_csv(seeddenialreasons.DENIAL_REASONS_FILE))
        )

    @pytest.mark.seeding
    def test_seed_layouts(self):
        self.seed_command(seedlayouts.Command)
        csv = seedlayouts.Command.read_csv(seedlayouts.LAYOUTS_FILE)
        html_layouts = os.listdir(os.path.join(BASE_DIR, "letter_templates", "templates", "letter_templates"))
        for row in csv:
            self.assertTrue(f"{row['filename']}.html" in html_layouts)
        self.assertEqual(LetterLayout.objects.count(), len(csv))

    @pytest.mark.seeding
    def test_seed_role_permissions(self):
        self.seed_command(seedrolepermissions.Command)
        self.assertTrue(Permission.objects.count() >= len(GovPermissions) + len(ExporterPermissions))

    @pytest.mark.seeding
    def test_seed_decisions(self):
        self.seed_command(seedfinaldecisions.Command)
        enum = AdviceType.choices
        self.assertEqual(Decision.objects.count(), len(enum))
        for key, _ in enum:
            self.assertTrue(
                Decision.objects.filter(id=AdviceType.ids[key], name=key).exists(), f"Decision {key} does not exist"
            )

    @pytest.mark.seeding
    def test_seed_letter_templates(self):
        # Since we are a migrating a letter template this command now requires an empty lettertemplate table
        LetterLayout.objects.all().delete()
        with NamedTemporaryFile(suffix=".csv", delete=True) as tmp_file:
            layout = LetterLayout.objects.create(name="layout1", filename="filename1")
            content = [
                "name,layout_id,visible_to_exporter,include_digital_signature,casetype_id",
                f"template1,{layout.id},true,true,00000000-0000-0000-0000-000000000004",
                f"template2,{layout.id},true,true,00000000-0000-0000-0000-000000000004",
            ]
            tmp_file.write(("\n".join(content)).encode("utf-8"))
            tmp_file.flush()
            seedlettertemplates.LETTER_TEMPLATES_FILE = tmp_file.name
            self.seed_command(seedlettertemplates.Command)

            self.assertEqual(LetterTemplate.objects.count(), 2)

            # running again with existing templates does nothing
            self.seed_command(seedlettertemplates.Command)
            self.assertEqual(LetterTemplate.objects.count(), 2)

    @pytest.mark.seeding
    @parameterized.expand(
        [
            ([{"email": "admin@example.co.uk", "role": "Super User"}],),
            ([{"email": "manager@example.co.uk", "role": "Manager", "first_name": "LU", "last_name": "Manager"}],),
            (
                [
                    {
                        "email": "senior_manager@example.co.uk",
                        "role": "Senior Manager",
                        "team_id": TeamIdEnum.LICENSING_UNIT,
                    }
                ],
            ),
            (
                [
                    {
                        "email": "case_officer@example.co.uk",
                        "role": "Case officer",
                        "team_id": TeamIdEnum.LICENSING_UNIT,
                        "default_queue": "00000000-0000-0000-0000-000000000004",
                    }
                ],
            ),
        ]
    )
    def test_seed_internal_users(self, data):
        os.environ["INTERNAL_USERS"] = json.dumps(data)

        self.seed_command(seedinternalusers.Command)

        for item in data:
            user = GovUser.objects.get(baseuser_ptr__email=item["email"])
            self.assertEqual(user.role.name, item["role"])
            self.assertEqual(str(user.team_id), item.get("team_id", Teams.ADMIN_TEAM_ID))
            self.assertEqual(str(user.default_queue), item.get("default_queue", ALL_CASES_QUEUE_ID))
