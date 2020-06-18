from applications.models import SiteOnApplication, GoodOnApplication
from compliance.helpers import generate_compliance_site_case
from compliance.models import ComplianceSiteCase
from goods.enums import GoodControlled
from goods.tests.factories import GoodFactory
from organisations.tests.factories import SiteFactory
from static.control_list_entries.factories import ControlListEntriesFactory
from test_helpers.clients import DataTestClient
from parameterized import parameterized


class ComplianceCreateTests(DataTestClient):
    def tests_OIEL_type(self):
        case = self.create_open_application_case(self.organisation)

        generate_compliance_site_case(case)

        self.assertTrue(ComplianceSiteCase.objects.exists())

    def tests_multi_site(self):
        case = self.create_open_application_case(self.organisation)

        # create and add 2nd site to application
        SiteOnApplication(site=SiteFactory(organisation=self.organisation), application=case).save()

        generate_compliance_site_case(case)

        self.assertEqual(ComplianceSiteCase.objects.count(), 2)

    def tests_multi_site_same_record_holder(self):
        case = self.create_open_application_case(self.organisation)

        # create and add 2nd site to application
        new_site = SiteFactory(organisation=self.organisation)
        new_site.site_records_located_at = self.organisation.primary_site
        new_site.save()
        SiteOnApplication(site=new_site, application=case).save()

        generate_compliance_site_case(case)

        self.assertEqual(ComplianceSiteCase.objects.count(), 1)

    def tests_siel_bad_control_code(self):
        case = self.create_standard_application_case(self.organisation)

        generate_compliance_site_case(case)

        self.assertFalse(ComplianceSiteCase.objects.exists())

    @parameterized.expand(
        [
            ("ML21", True),
            ("ML22", True),
            ("ML2", False),
            ("ML21abcde", True),
            ("0D", True),
            ("00D", False),
            ("9E13", True),
        ]
    )
    def tests_siel_good_control_code(self, control_code, exists):
        case = self.create_standard_application_case(self.organisation)

        ControlListEntriesFactory(rating=control_code)
        good = GoodFactory(
            organisation=self.organisation, is_good_controlled=GoodControlled.YES, control_list_entries=[control_code],
        )
        GoodOnApplication(application_id=case.id, good=good, licenced_quantity=5, licenced_value=10, usage=0).save()

        generate_compliance_site_case(case)

        self.assertEqual(ComplianceSiteCase.objects.exists(), exists)

    def test_multiple_cases_creates_one_compliance_case(self):
        # Both cases uses the organisation primary site by default on creation
        case = self.create_open_application_case(self.organisation)
        case_2 = self.create_open_application_case(self.organisation)
        generate_compliance_site_case(case)
        generate_compliance_site_case(case_2)

        self.assertEqual(ComplianceSiteCase.objects.count(), 1)

    def test_bad_case_type(self):
        case = self.create_end_user_advisory_case("note", "reasoning", self.organisation)

        generate_compliance_site_case(case)

        self.assertFalse(ComplianceSiteCase.objects.exists())

    def test_different_record_holding_site(self):
        case = self.create_open_application_case(self.organisation)

        record_site = SiteFactory()
        self.organisation.primary_site.site_records_located_at = record_site
        self.organisation.primary_site.save()

        generate_compliance_site_case(case)

        self.assertEqual(ComplianceSiteCase.objects.count(), 1)
        self.assertTrue(ComplianceSiteCase.objects.filter(site_id=record_site.id).exists())

    def test_multiple_sites_one_already_contains_compliance_case(self):
        case = self.create_open_application_case(self.organisation)
        # compliance case created for organisation primary site
        generate_compliance_site_case(case)

        self.assertEqual(ComplianceSiteCase.objects.count(), 1)

        case_2 = self.create_open_application_case(self.organisation)

        # create and add 2nd site to application
        new_site = SiteFactory(organisation=self.organisation)
        SiteOnApplication(site=new_site, application=case_2).save()

        generate_compliance_site_case(case_2)

        self.assertEqual(ComplianceSiteCase.objects.count(), 2)
