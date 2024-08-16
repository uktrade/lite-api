import pytest

from django_test_migrations.migrator import Migrator


@pytest.mark.django_db()
def test_copy_denial_reasons():
    migrator = Migrator(database="default")

    print("apply initial migration")
    old_state = migrator.apply_initial_migration(
        [("cases", "0066_delete_casereviewdate"), ("organisations", "0003_organisation_status")]
    )
    print("apply initial migration - done")

    # Create test objects
    # We can't use factories here so need to create each
    # dependent object explicitly
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
    DenialReason = old_state.apps.get_model("denial_reasons", "DenialReason")
    denial_reason = DenialReason.objects.get(id="1")

    # Create advice object
    Advice = old_state.apps.get_model("cases", "Advice")
    advice = Advice.objects.create(case_id=standard_application.id, user=gov_user, type="refuse", level="user")

    assert Advice.objects.all().count() == 1

    advice.denial_reasons.set([denial_reason])

    assert advice.denial_reasons.all().count() == 1

    print("apply tested migration")
    new_state = migrator.apply_tested_migration(("cases", "0068_copy_denial_reasons"))

    AdviceDenialReason = new_state.apps.get_model("cases", "AdviceDenialReason")

    # Assert that test objects are linked as expected
    assert AdviceDenialReason.objects.all().count() == 1
    advice_denial_reason = AdviceDenialReason.objects.get()
    assert advice_denial_reason.advice.id == advice.id
    assert advice_denial_reason.denial_reason.uuid == denial_reason.uuid

    migrator.reset()
