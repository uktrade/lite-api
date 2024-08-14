import pytest

from django_test_migrations.migrator import Migrator


@pytest.mark.django_db()
def test_copy_denial_reasons():
    migrator = Migrator(database="default")

    old_state = migrator.apply_initial_migration(
        [
            ("cases", "0067_advicedenialreason_advice_denial_reasons_uuid"),
            ("denial_reasons", "0007_alter_denialreason_uuid"),
            ("countries", "0006_update_trading_country_code"),
            ("organisations", "0014_alter_organisation_status"),
        ]
    )

    # create some test objects
    Country = old_state.apps.get_model("countries", "Country")
    country = Country.objects.get(pk="GB")

    Address = old_state.apps.get_model("addresses", "Address")
    address = Address.objects.create(country=country)

    Site = old_state.apps.get_model("organisations", "Site")
    site = Site.objects.create(name="Site Name", address=address, organisation=None)

    Organisation = old_state.apps.get_model("organisations", "Organisation")
    organisation = Organisation.objects.create(
        name="Organisation Name", type="commercial", status="active", primary_site=site
    )

    CaseStatus = old_state.apps.get_model("statuses", "CaseStatus")
    submitted = CaseStatus.objects.get(status="submitted")

    CaseType = old_state.apps.get_model("cases", "CaseType")
    siel = CaseType.objects.get(reference="siel")

    StandardApplication = old_state.apps.get_model("applications", "StandardApplication")
    standard_application = StandardApplication.objects.create(
        status=submitted, case_type=siel, organisation_id=organisation.id
    )

    BaseUser = old_state.apps.get_model("users", "BaseUser")
    base_user = BaseUser.objects.create(type="Internal", email="example@example.com")  # /PS-IGNORE

    Team = old_state.apps.get_model("teams", "Team")
    admin = Team.objects.get(name="Admin")

    Role = old_state.apps.get_model("users", "Role")
    role = Role.objects.create(id="00000000-0000-0000-0000-000000000001", name="Default", type="internal")

    GovUser = old_state.apps.get_model("users", "GovUser")
    gov_user = GovUser.objects.create(baseuser_ptr_id=base_user.id, team_id=admin.id, role_id=role.id)

    Advice = old_state.apps.get_model("cases", "Advice")
    advice = Advice.objects.create(case_id=standard_application.id, user=gov_user, type="refuse", level="user")

    assert advice

    # DenialReason = old_state.apps.get_model("denial_reasons", "DenialReason")

    # # assert things maybe

    # new_state = migrator.apply_tested_migration(("cases", "0068_copy_denial_reasons"))
    # AdviceDenialReason = new_state.apps.get_model("cases", "AdviceDenialReason")

    # # assert that your test objects are linked as expected
