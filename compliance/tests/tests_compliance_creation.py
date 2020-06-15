from applications.models import SiteOnApplication, GoodOnApplication
from compliance.helpers import generate_compliance
from compliance.models import ComplianceSiteCase
from goods.enums import GoodControlled
from goods.tests.factories import GoodFactory
from organisations.tests.factories import SiteFactory
from static.control_list_entries.factories import ControlListEntriesFactory
from test_helpers.clients import DataTestClient


class ComplianceCreateTests(DataTestClient):
    def tests_OIEL_type(self):
        case = self.create_open_application_case(self.organisation)

        generate_compliance(case)

        self.assertTrue(ComplianceSiteCase.objects.exists())

    def tests_multi_site(self):
        case = self.create_open_application_case(self.organisation)

        # create and add 2nd site to application
        SiteOnApplication(site=SiteFactory(organisation=self.organisation), application=case).save()

        generate_compliance(case)

        self.assertEqual(ComplianceSiteCase.objects.count(), 2)

    def tests_multi_site_same_record_holder(self):
        case = self.create_open_application_case(self.organisation)

        # create and add 2nd site to application
        new_site = SiteFactory(organisation=self.organisation)
        new_site.site_records_located_at = self.organisation.primary_site
        new_site.save()
        SiteOnApplication(site=new_site, application=case).save()

        generate_compliance(case)

        self.assertEqual(ComplianceSiteCase.objects.count(), 1)

    def tests_siel_bad_control_code(self):
        case = self.create_standard_application_case(self.organisation)

        generate_compliance(case)

        self.assertFalse(ComplianceSiteCase.objects.exists())

    def tests_siel_good_control_code(self):
        case = self.create_standard_application_case(self.organisation)

        ControlListEntriesFactory(rating="ML21a")
        good = GoodFactory(
            organisation=self.organisation, is_good_controlled=GoodControlled.YES, control_list_entries=["ML21a"],
        )
        GoodOnApplication(application_id=case.id, good=good).save()

        generate_compliance(case)

        self.assertTrue(ComplianceSiteCase.objects.exists())

    def test_multiple_cases_creates_one_compliance_case(self):
        # Both cases uses the organisation primary site by default on creation
        case = self.create_open_application_case(self.organisation)
        case_2 = self.create_open_application_case(self.organisation)
        generate_compliance(case)
        generate_compliance(case_2)

        self.assertEqual(ComplianceSiteCase.objects.count(), 1)

    def test_bad_case_type(self):
        case = self.create_end_user_advisory_case("note", "reasoning", self.organisation)

        generate_compliance(case)

        self.assertFalse(ComplianceSiteCase.objects.exists())
