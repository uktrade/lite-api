from django_test_migrations.contrib.unittest_case import MigratorTestCase

from api.core.constants import Roles


class TestAdviceTeamMigration(MigratorTestCase):
    migrate_from = ("cases", "0063_ecjuquery_chaser_email_sent_on")
    migrate_to = ("cases", "0064_update_teams_on_advice")

    def prepare(self):
        Role = self.old_state.apps.get_model("users", "Role")
        Role.objects.create(id=Roles.INTERNAL_DEFAULT_ROLE_ID)

        Team = self.old_state.apps.get_model("teams", "Team")
        self.a_team = Team.objects.create(name="a_team")
        self.b_team = Team.objects.create(name="b_team")

        BaseUser = self.old_state.apps.get_model("users", "BaseUser")
        a_team_base_user = BaseUser.objects.create(email="a_team_base_user@example.com")  # /PS-IGNORE
        b_team_base_user = BaseUser.objects.create(email="b_team_base_user@example.com")  # /PS-IGNORE

        GovUser = self.old_state.apps.get_model("users", "GovUser")
        a_team_user = GovUser.objects.create(
            baseuser_ptr=a_team_base_user,
            team=self.a_team,
        )
        b_team_user = GovUser.objects.create(
            baseuser_ptr=b_team_base_user,
            team=self.b_team,
        )

        Organisation = self.old_state.apps.get_model("organisations", "Organisation")
        organisation = Organisation.objects.create(name="test")

        CaseType = self.old_state.apps.get_model("cases", "CaseType")
        case_type = CaseType.objects.get(pk="00000000-0000-0000-0000-000000000004")

        Case = self.old_state.apps.get_model("cases", "Case")
        case = Case.objects.create(
            case_type=case_type,
            organisation=organisation,
        )

        Advice = self.old_state.apps.get_model("cases", "Advice")
        self.user_advice_with_same_team = Advice.objects.create(
            case=case,
            team=self.a_team,
            user=a_team_user,
        )
        self.user_advice_with_different_team = Advice.objects.create(
            case=case,
            team=self.a_team,
            user=b_team_user,
        )
        self.user_advice_without_team = Advice.objects.create(
            case=case,
            team=None,
            user=a_team_user,
        )

    def test_migration_0064_update_teams_on_advice(self):
        self.user_advice_with_same_team.refresh_from_db()
        self.assertEqual(
            self.user_advice_with_same_team.team,
            self.a_team,
        )

        self.user_advice_with_different_team.refresh_from_db()
        self.assertEqual(
            self.user_advice_with_different_team.team,
            self.a_team,
        )

        self.user_advice_without_team.refresh_from_db()
        self.assertEqual(
            self.user_advice_without_team.team,
            self.a_team,
        )
