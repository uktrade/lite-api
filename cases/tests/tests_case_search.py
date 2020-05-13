from cases.models import Case
from cases.tests.factories import SiteOnApplicationFactory, ApplicationFactory, GoodOnApplicationFactory, \
    CountryFactory, CountryOnApplicationFactory
from flags.tests.factories import FlagFactory
from goods.enums import GoodControlled
from goods.tests.factories import GoodFactory
from static.control_list_entries.models import ControlListEntry
from test_helpers.clients import DataTestClient
from difflib import SequenceMatcher


class FilterAndSortTests(DataTestClient):
    def setUp(self):
        super().setUp()

    def test_filter_by_exporter_site_name(self):
        site_on_application_1 = SiteOnApplicationFactory()
        site_on_application_2 = SiteOnApplicationFactory()
        site_on_application_3 = SiteOnApplicationFactory(application=site_on_application_2.application)

        qs_1 = Case.objects.search(exporter_site_name=site_on_application_1.site.name)
        qs_2 = Case.objects.search(exporter_site_name=site_on_application_2.site.name)
        qs_3 = Case.objects.search(exporter_site_name=site_on_application_3.site.name)

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(site_on_application_2.application.pk, site_on_application_3.application.pk)
        self.assertNotEqual(site_on_application_1.application.pk, site_on_application_2.application.pk)
        self.assertNotEqual(site_on_application_1.site.name, site_on_application_2.site.name)

    def test_filter_with_organisation_name(self):
        application_1 = ApplicationFactory()
        application_2 = ApplicationFactory()

        qs_1 = Case.objects.search(organisation_name=application_1.organisation.name)
        qs_2 = Case.objects.search(organisation_name=application_2.organisation.name)

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_1.first().pk, application_1.pk)
        self.assertEqual(qs_2.first().pk, application_2.pk)

    def test_filter_with_case_reference_code(self):
        application_1 = ApplicationFactory()
        application_2 = ApplicationFactory()

        qs_1 = Case.objects.search(case_reference=application_1.reference_code)
        qs_2 = Case.objects.search(case_reference=application_1.reference_code[4:])
        qs_3 = Case.objects.search(case_reference=application_2.reference_code)
        qs_4 = Case.objects.search(case_reference=application_2.reference_code[4:])

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_4.count(), 1)

        self.assertEqual(qs_1.first().pk, application_1.pk)
        self.assertEqual(qs_2.first().pk, application_1.pk)
        self.assertEqual(qs_3.first().pk, application_2.pk)
        self.assertEqual(qs_4.first().pk, application_2.pk)

        # Search on common substring of both application references
        match = (
            SequenceMatcher(None, application_1.reference_code, application_2.reference_code)
            .find_longest_match(0, len(application_1.reference_code), 0, len(application_2.reference_code))
        )

        qs_5 = Case.objects.search(case_reference=application_1.reference_code[match.a: match.a + match.size])

        self.assertEqual(qs_5.count(), 2)

    def test_filter_by_good_control_list_entries(self):
        application = ApplicationFactory()
        good = GoodFactory(organisation=application.organisation, is_good_controlled=GoodControlled.YES, control_list_entries=["ML1a"])
        GoodOnApplicationFactory(application=application, good=good)

        qs_1 = Case.objects.search(control_list_entries=[])
        qs_2 = Case.objects.search(control_list_entries=["ML1b"])
        qs_3 = Case.objects.search(control_list_entries=["ML1a"])
        qs_4 = Case.objects.search(control_list_entries=["ML1a", "ML1b"])

        self.assertEqual(qs_1.count(), 0)
        self.assertEqual(qs_2.count(), 0)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_4.count(), 1)

    def test_filter_by_flags(self):
        flag_1 = FlagFactory(name="Name_1", level="Destination", team=self.gov_user.team, priority=9)
        flag_2 = FlagFactory(name="Name_2", level="Destination", team=self.gov_user.team, priority=10)
        application = ApplicationFactory()
        application.flags.add(flag_2)

        qs_1 = Case.objects.search(flags=[flag_1.name])
        qs_2 = Case.objects.search(flags=[flag_2.name])

        self.assertEqual(qs_1.count(), 0)
        self.assertEqual(qs_2.count(), 1)

    def test_filter_by_country(self):
        """
        What qualifies as a country on a case?
        """
        #
        # country_on_application = CountryOnApplicationFactory()
        #
        # qs_1 = Case.objects.search(country=country_on_application.country.name)
        #
        # self.assertEqual(qs_1.count(), 1)
