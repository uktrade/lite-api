import os

from cases.models import CaseType
from conf.constants import GovPermissions, ExporterPermissions
from conf.settings import BASE_DIR
from flags.models import Flag
from organisations.models import Organisation, Site
from static.control_list_entries.models import ControlListEntry
from static.countries.models import Country
from static.denial_reasons.models import DenialReason
from static.letter_layouts.models import LetterLayout
from static.management.SeedCommand import SeedCommandTest
from static.management.commands import seedlayouts, seedcasestatuses, seedcasetypes, seedcontrollistentries, \
    seedcountries, seeddenialreasons, seedgovusers, seedorgusers, seedrolepermissions, seedsystemflags
from static.statuses.models import CaseStatus, CaseStatusCaseType
from users.models import Permission, GovUser, Role, ExporterUser, UserOrganisationRelationship


class SeedingTests(SeedCommandTest):
    def test_seed_case_statuses(self):
        self.seed_command(seedcasestatuses.Command)
        self.assertEqual(CaseStatus.objects.count(), len(seedcasestatuses.Command.read_csv(seedcasestatuses.STATUSES_FILE)))
        self.assertEqual(CaseStatusCaseType.objects.count(), len(seedcasestatuses.Command.read_csv(seedcasestatuses.STATUS_ON_TYPE_FILE)))

    def test_seed_case_types(self):
        self.seed_command(seedcasetypes.Command)
        self.assertEqual(CaseType.objects.count(), len(seedcasestatuses.Command.read_csv(seedcasetypes.CASE_TYPES_FILE)))

    def test_seed_control_list_entries(self):
        self.seed_command(seedcontrollistentries.Command)
        self.assertTrue(ControlListEntry.objects.count() > 3000)

    def test_seed_countries(self):
        self.seed_command(seedcountries.Command)
        self.assertEqual(Country.objects.count(), len(seedcountries.Command.read_csv(seedcountries.COUNTRIES_FILE)))

    def test_seed_denial_reasons(self):
        self.seed_command(seeddenialreasons.Command)
        self.assertEqual(DenialReason.objects.count(), len(seeddenialreasons.Command.read_csv(seeddenialreasons.DENIAL_REASONS_FILE)))

    def test_seed_gov_user(self):
        self.seed_command(seedrolepermissions.Command)
        self.seed_command(seedgovusers.Command)
        self.assertTrue(Permission.objects)
        self.assertTrue(GovUser.objects)
        self.assertTrue(Role.objects)

    def test_seed_layouts(self):
        self.seed_command(seedlayouts.Command)
        csv = seedlayouts.Command.read_csv(seedlayouts.LAYOUTS_FILE)
        html_layouts = os.listdir(os.path.join(BASE_DIR, "letter_templates", "layouts"))
        for row in csv:
            self.assertTrue(f"{row['filename']}.html" in html_layouts)
        self.assertEqual(LetterLayout.objects.count(), len(csv))

    def test_seed_org_users(self):
        self.seed_command(seedrolepermissions.Command)
        self.seed_command(seedcountries.Command)
        self.seed_command(seedorgusers.Command)
        self.assertTrue(Organisation.objects)
        self.assertTrue(Site.objects)
        num_exporter_users = len(seedorgusers._get_exporter_users())
        self.assertEqual(num_exporter_users, ExporterUser.objects.count())
        self.assertTrue(num_exporter_users <= UserOrganisationRelationship.objects.count())

    def test_seed_role_permissions(self):
        self.seed_command(seedrolepermissions.Command)
        self.assertTrue(Permission.objects.count() >= len(GovPermissions) + len(ExporterPermissions))

    def test_seed_system_flags(self):
        self.seed_command(seedsystemflags.Command)
        self.assertTrue(Flag.objects.count(), len(seedlayouts.Command.read_csv(seedsystemflags.SYSTEM_FLAGS_FILE)))
