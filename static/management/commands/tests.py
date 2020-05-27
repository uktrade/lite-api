import os

from django.test import tag

from cases.enums import CaseTypeEnum
from cases.models import CaseType
from conf.constants import GovPermissions, ExporterPermissions
from conf.settings import BASE_DIR
from flags.models import Flag
from queues.models import Queue
from static.control_list_entries.models import ControlListEntry
from static.countries.models import Country
from cases.enums import AdviceType
from static.decisions.models import Decision
from static.denial_reasons.models import DenialReason
from static.letter_layouts.models import LetterLayout
from static.management.SeedCommand import SeedCommandTest
from static.management.commands import (
    seedlayouts,
    seedcasestatuses,
    seedcasetypes,
    seedcontrollistentries,
    seedcountries,
    seeddenialreasons,
    seedrolepermissions,
    seedadminteam,
    seedflags,
    seedinternaldemodata,
    seedfinaldecisions,
)
from static.statuses.models import CaseStatus, CaseStatusCaseType
from teams.models import Team
from users.models import Permission


@tag("seeding")
class SeedingTests(SeedCommandTest):
    def test_seed_case_types(self):
        self.seed_command(seedcasetypes.Command)
        enum = CaseTypeEnum.CASE_TYPE_LIST
        self.assertEqual(CaseType.objects.count(), len(enum))
        for item in enum:
            self.assertTrue(CaseType.objects.get(id=item.id))

    def test_seed_case_statuses(self):
        self.seed_command(seedcasetypes.Command)
        self.seed_command(seedcasestatuses.Command)
        self.assertEqual(
            CaseStatus.objects.count(), len(seedcasestatuses.Command.read_csv(seedcasestatuses.STATUSES_FILE))
        )

        case_type_list = CaseTypeEnum.CASE_TYPE_LIST
        counter = 0
        for case_type in case_type_list:
            for key, value in seedcasestatuses.Command.STATUSES_ON_CASE_TYPES.items():
                if case_type.sub_type in value or case_type.type in value:
                    counter += 1

        self.assertEqual(CaseStatusCaseType.objects.all().count(), counter)

    def test_seed_control_list_entries(self):
        self.seed_command(seedcontrollistentries.Command)
        self.assertEqual(ControlListEntry.objects.count(), 2902)

    def test_seed_countries(self):
        self.seed_command(seedcountries.Command)
        self.assertEqual(
            Country.include_special_countries.count(), len(seedcountries.Command.read_csv(seedcountries.COUNTRIES_FILE))
        )

    def test_seed_denial_reasons(self):
        self.seed_command(seeddenialreasons.Command)
        self.assertEqual(
            DenialReason.objects.count(), len(seeddenialreasons.Command.read_csv(seeddenialreasons.DENIAL_REASONS_FILE))
        )

    def test_seed_layouts(self):
        self.seed_command(seedlayouts.Command)
        csv = seedlayouts.Command.read_csv(seedlayouts.LAYOUTS_FILE)
        html_layouts = os.listdir(os.path.join(BASE_DIR, "letter_templates", "layouts"))
        for row in csv:
            self.assertTrue(f"{row['filename']}.html" in html_layouts)
        self.assertEqual(LetterLayout.objects.count(), len(csv))

    def test_seed_role_permissions(self):
        self.seed_command(seedrolepermissions.Command)
        self.assertTrue(Permission.objects.count() >= len(GovPermissions) + len(ExporterPermissions))

    def test_seed_flags(self):
        self.seed_command(seedrolepermissions.Command)
        self.seed_command(seedadminteam.Command)
        self.seed_command(seedflags.Command)
        for flag in seedflags.Command.read_csv(seedflags.FLAGS_FILE):
            self.assertTrue(Flag.objects.filter(name=flag["name"]).exists(), f"Flag {flag['name']} does not exist")

    def test_seed_demo_data(self):
        self.seed_command(seedadminteam.Command)
        self.seed_command(seedinternaldemodata.Command)
        for team in seedinternaldemodata.Command.read_csv(seedinternaldemodata.TEAMS_FILE):
            self.assertTrue(Team.objects.filter(name=team["name"]).exists(), f"Team {team['name']} does not exist")
        for queue in seedinternaldemodata.Command.read_csv(seedinternaldemodata.QUEUES_FILE):
            self.assertTrue(Queue.objects.filter(name=queue["name"]).exists(), f"Queue {queue['name']} does not exist")
        for flag in seedinternaldemodata.Command.read_csv(seedinternaldemodata.FLAGS_FILE):
            self.assertTrue(Flag.objects.filter(name=flag["name"]).exists(), f"Flag {flag['name']} does not exist")

    def test_seed_decisions(self):
        self.seed_command(seedfinaldecisions.Command)
        enum = AdviceType.choices
        self.assertEqual(Decision.objects.count(), len(enum))
        for key, _ in enum:
            self.assertTrue(
                Decision.objects.filter(id=AdviceType.ids[key], name=key).exists(), f"Decision {key} does not exist"
            )
