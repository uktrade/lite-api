import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase
from api.staticdata.units.enums import Units


def old_state_good_on_application_factory(self, unit):
    CaseStatus = self.old_state.apps.get_model("statuses", "CaseStatus")  # noqa N806
    Good = self.old_state.apps.get_model("goods", "Good")  # noqa N806
    GoodOnApplication = self.old_state.apps.get_model("applications", "GoodOnApplication")  # noqa N806
    StandardApplication = self.old_state.apps.get_model("applications", "StandardApplication")  # noqa N806
    Organisation = self.old_state.apps.get_model("organisations", "Organisation")  # noqa N806
    Case = self.old_state.apps.get_model("cases", "Case")  # noqa N806
    CaseType = self.old_state.apps.get_model("cases", "CaseType")  # noqa N806

    case_status = CaseStatus.objects.get(status="submitted")
    case_type = CaseType.objects.get(type="application", reference="oiel", sub_type="open")

    organisation = Organisation.objects.create(name="test")
    case = Case.objects.create(case_type=case_type, organisation=organisation)
    application = StandardApplication.objects.create(
        organisation=organisation, case_type=case_type, case=case, status=case_status
    )
    good = Good.objects.create(name="test", organisation=organisation)
    good_on_application = GoodOnApplication.objects.create(application=application, good=good, unit=unit)
    return good_on_application


@pytest.mark.django_db()
class ChangeLegacyUnitCodesTestCase(MigratorTestCase):
    migrate_from = ("applications", "0082_alter_goodonapplication_unit")
    migrate_to = ("applications", "0083_amend_existing_goodonapplication_unit_legacy_codes")

    old_unit_codes = ["MIM", "MCM", "MIR", "MCR"]
    new_unit_codes = [Units.MGM, Units.MCG, Units.MLT, Units.MCL]

    def prepare(self):
        for old_unit_code in self.old_unit_codes:
            old_state_good_on_application_factory(self, unit=old_unit_code)

    def test_change_legacy_unit_codes(self):
        GoodOnApplication = self.new_state.apps.get_model("applications", "GoodOnApplication")
        new_good_on_applications = GoodOnApplication.objects.all()

        assert all(
            new_good_on_application.unit not in self.old_unit_codes
            for new_good_on_application in new_good_on_applications
        )
        assert all(
            new_good_on_application.unit in self.new_unit_codes for new_good_on_application in new_good_on_applications
        )
