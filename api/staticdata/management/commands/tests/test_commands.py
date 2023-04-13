import os
import pytest

from django.conf import settings
from tempfile import NamedTemporaryFile

from api.cases.enums import CaseTypeEnum
from api.cases.models import CaseType
from api.core.constants import GovPermissions, ExporterPermissions
from api.conf.settings import BASE_DIR
from api.letter_templates.models import LetterTemplate
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.countries.models import Country
from api.cases.enums import AdviceType
from api.staticdata.decisions.models import Decision
from api.staticdata.denial_reasons.models import DenialReason
from api.staticdata.letter_layouts.models import LetterLayout
from api.staticdata.management.SeedCommand import SeedCommandTest
from api.staticdata.management.commands import (
    seedlayouts,
    seedcasestatuses,
    seedcasetypes,
    seedcontrollistentries,
    seedcountries,
    seeddenialreasons,
    seedlettertemplates,
    seedrolepermissions,
    seedfinaldecisions,
)
from api.staticdata.statuses.models import CaseStatus, CaseStatusCaseType
from api.teams.models import Team
from api.users.models import Permission


class SeedingTests(SeedCommandTest):
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
    def test_seed_control_list_entries(self):
        self.seed_command(seedcontrollistentries.Command)
        self.assertEqual(ControlListEntry.objects.count(), 2943)

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
