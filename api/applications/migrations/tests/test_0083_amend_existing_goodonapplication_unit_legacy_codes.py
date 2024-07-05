import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase
from api.staticdata.units.enums import Units


def old_state_good_on_application_factory(self, unit):
    CaseStatus = self.old_state.apps.get_model("statuses", "CaseStatus")
    Good = self.old_state.apps.get_model("goods", "Good")
    GoodOnApplication = self.old_state.apps.get_model("applications", "GoodOnApplication")
    StandardApplication = self.old_state.apps.get_model("applications", "StandardApplication")
    Organisation = self.old_state.apps.get_model("organisations", "Organisation")
    Case = self.old_state.apps.get_model("cases", "Case")
    CaseType = self.old_state.apps.get_model("cases", "CaseType")

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

    def prepare(self):

        self.expected_mappings = {
            "MIM": Units.MGM,
            "MCM": Units.MCG,
            "MIR": Units.MLT,
            "MCR": Units.MCL,
            "NAR": Units.NAR,
        }

        self.test_records = [
            {
                "id": old_state_good_on_application_factory(self, unit=old_unit).id,
                "expected_unit": new_unit,
            }
            for old_unit, new_unit in self.expected_mappings.items()
        ]

    def test_change_legacy_unit_codes(self):

        GoodOnApplication = self.new_state.apps.get_model("applications", "GoodOnApplication")

        assert len(self.test_records) == len(self.expected_mappings)

        for test_record in self.test_records:
            good_on_application = GoodOnApplication.objects.get(id=test_record["id"])

            assert good_on_application.unit == test_record["expected_unit"]
