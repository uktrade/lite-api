from applications.models import SiteOnApplication
from compliance.helpers import generate_compliance
from compliance.models import ComplianceSiteCase
from organisations.tests.factories import SiteFactory
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
