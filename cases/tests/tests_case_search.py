from difflib import SequenceMatcher

from django.utils import timezone

from cases.enums import AdviceType
from cases.models import Case
from cases.tests.factories import (
    SiteOnApplicationFactory, ApplicationFactory, GoodOnApplicationFactory, TeamAdviceFactory, FinalAdviceFactory,
    PartyOnApplicationFactory, PartyFactory
)
from flags.tests.factories import FlagFactory
from goods.enums import GoodControlled
from goods.tests.factories import GoodFactory
from test_helpers.clients import DataTestClient


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

    def test_filter_by_good_control_list_entry(self):
        application = ApplicationFactory()
        good = GoodFactory(organisation=application.organisation, is_good_controlled=GoodControlled.YES, control_list_entries=["ML1a"])
        GoodOnApplicationFactory(application=application, good=good)

        qs_1 = Case.objects.search(control_list_entry="")
        qs_2 = Case.objects.search(control_list_entry="ML1b")
        qs_3 = Case.objects.search(control_list_entry="ML1a")

        self.assertEqual(qs_1.count(), 0)
        self.assertEqual(qs_2.count(), 0)
        self.assertEqual(qs_3.count(), 1)

    def test_filter_by_flags(self):
        flag_1 = FlagFactory(name="Name_1", level="Destination", team=self.gov_user.team, priority=9)
        flag_2 = FlagFactory(name="Name_2", level="Destination", team=self.gov_user.team, priority=10)
        application_1 = ApplicationFactory()
        application_1.flags.add(flag_1)
        application_2 = ApplicationFactory()
        application_2.flags.add(flag_2)
        application_3 = ApplicationFactory()
        application_3.flags.add(flag_2)

        qs_1 = Case.objects.search(flags=[flag_1.name])
        qs_2 = Case.objects.search(flags=[flag_2.name])

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 2)

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

    def test_filter_by_team_advice(self):
        application = ApplicationFactory()
        good = GoodFactory(organisation=application.organisation)
        TeamAdviceFactory(user=self.gov_user, team=self.team, case=application, good=good, type=AdviceType.APPROVE)

        qs_1 = Case.objects.search(team_advice_type=AdviceType.CONFLICTING)
        qs_2 = Case.objects.search(team_advice_type=AdviceType.APPROVE)

        self.assertEqual(qs_1.count(), 0)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_2.first().pk, application.pk)

    def test_filter_by_final_advice(self):
        application = ApplicationFactory()
        good = GoodFactory(organisation=application.organisation)
        FinalAdviceFactory(user=self.gov_user, team=self.team, case=application, good=good, type=AdviceType.APPROVE)

        qs_1 = Case.objects.search(final_advice_type=AdviceType.CONFLICTING)
        qs_2 = Case.objects.search(final_advice_type=AdviceType.APPROVE)

        self.assertEqual(qs_1.count(), 0)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_2.first().pk, application.pk)

    def test_filter_sla_days_range(self):
        application_1 = ApplicationFactory(sla_remaining_days=1)
        application_2 = ApplicationFactory(sla_remaining_days=3)
        application_3 = ApplicationFactory(sla_remaining_days=5)

        qs_1 = Case.objects.search(min_sla_days_remaining=0, max_sla_days_remaining=2)
        qs_2 = Case.objects.search(min_sla_days_remaining=2, max_sla_days_remaining=4)
        qs_3 = Case.objects.search(min_sla_days_remaining=4, max_sla_days_remaining=6)
        qs_4 = Case.objects.search(min_sla_days_remaining=0, max_sla_days_remaining=6)
        qs_5 = Case.objects.search(max_sla_days_remaining=2)
        qs_6 = Case.objects.search(min_sla_days_remaining=4)

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_4.count(), 3)
        self.assertEqual(qs_5.count(), 1)
        self.assertEqual(qs_6.count(), 1)
        self.assertEqual(qs_1.first().pk, application_1.pk)
        self.assertEqual(qs_2.first().pk, application_2.pk)
        self.assertEqual(qs_3.first().pk, application_3.pk)
        self.assertEqual(qs_5.first().pk, application_1.pk)
        self.assertEqual(qs_6.first().pk, application_3.pk)

    def test_filter_submitted_at_range(self):
        day_1 = timezone.datetime(day=10, month=10, year=2020)
        day_2 = timezone.datetime(day=11, month=10, year=2020)
        day_3 = timezone.datetime(day=12, month=10, year=2020)
        day_4 = timezone.datetime(day=13, month=10, year=2020)
        day_5 = timezone.datetime(day=14, month=10, year=2020)
        day_6 = timezone.datetime(day=15, month=10, year=2020)
        day_7 = timezone.datetime(day=16, month=10, year=2020)

        application_1 = ApplicationFactory(submitted_at=day_2)
        application_2 = ApplicationFactory(submitted_at=day_4)
        application_3 = ApplicationFactory(submitted_at=day_6)

        qs_1 = Case.objects.search(submitted_from=day_1.date(), submitted_to=day_3.date())
        qs_2 = Case.objects.search(submitted_from=day_3.date(), submitted_to=day_5.date())
        qs_3 = Case.objects.search(submitted_from=day_5.date(), submitted_to=day_7.date())
        qs_4 = Case.objects.search(submitted_from=day_2.date(), submitted_to=day_6.date())
        qs_5 = Case.objects.search(submitted_from=day_1.date())
        qs_6 = Case.objects.search(submitted_to=day_7.date())

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_4.count(), 3)
        self.assertEqual(qs_5.count(), 3)
        self.assertEqual(qs_6.count(), 3)
        self.assertEqual(qs_1.first().pk, application_1.pk)
        self.assertEqual(qs_2.first().pk, application_2.pk)
        self.assertEqual(qs_3.first().pk, application_3.pk)

    def test_filter_finalised_at_range(self):
        day_1 = timezone.datetime(day=10, month=10, year=2020)
        day_2 = timezone.datetime(day=11, month=10, year=2020)
        day_3 = timezone.datetime(day=12, month=10, year=2020)
        day_4 = timezone.datetime(day=13, month=10, year=2020)
        day_5 = timezone.datetime(day=14, month=10, year=2020)
        day_6 = timezone.datetime(day=15, month=10, year=2020)
        day_7 = timezone.datetime(day=16, month=10, year=2020)

        application_1 = ApplicationFactory(submitted_at=day_2)
        application_2 = ApplicationFactory(submitted_at=day_4)
        application_3 = ApplicationFactory(submitted_at=day_6)

        qs_1 = Case.objects.search(submitted_from=day_1.date(), submitted_to=day_3.date())
        qs_2 = Case.objects.search(submitted_from=day_3.date(), submitted_to=day_5.date())
        qs_3 = Case.objects.search(submitted_from=day_5.date(), submitted_to=day_7.date())
        qs_4 = Case.objects.search(submitted_from=day_2.date(), submitted_to=day_6.date())
        qs_5 = Case.objects.search(submitted_from=day_1.date())
        qs_6 = Case.objects.search(submitted_to=day_7.date())

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_4.count(), 3)
        self.assertEqual(qs_5.count(), 3)
        self.assertEqual(qs_6.count(), 3)
        self.assertEqual(qs_1.first().pk, application_1.pk)
        self.assertEqual(qs_2.first().pk, application_2.pk)
        self.assertEqual(qs_3.first().pk, application_3.pk)

    def test_filter_by_party_name(self):
        poa_1 = PartyOnApplicationFactory(party=PartyFactory(name="Steven Smith"))
        poa_2 = PartyOnApplicationFactory(party=PartyFactory(name="Steven Jones"))
        poa_3 = PartyOnApplicationFactory(party=PartyFactory(name="Jenny"))

        qs_1 = Case.objects.search(party_name=poa_1.party.name)
        qs_2 = Case.objects.search(party_name=poa_2.party.name)
        qs_3 = Case.objects.search(party_name=poa_3.party.name)
        qs_4 = Case.objects.search(party_name="Steven")

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_4.count(), 2)
        self.assertEqual(qs_1.first().pk, poa_1.application.pk)
        self.assertEqual(qs_2.first().pk, poa_2.application.pk)
        self.assertEqual(qs_3.first().pk, poa_3.application.pk)

    def test_filter_by_party_address(self):
        poa_1 = PartyOnApplicationFactory()
        poa_2 = PartyOnApplicationFactory()
        poa_3 = PartyOnApplicationFactory()

        qs_1 = Case.objects.search(party_address=poa_1.party.address)
        qs_2 = Case.objects.search(party_address=poa_2.party.address)
        qs_3 = Case.objects.search(party_address=poa_3.party.address)
        qs_4 = Case.objects.search(party_address=poa_2.party.address[0:int(len(poa_2.party.address) / 2)])

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_4.count(), 1)
        self.assertEqual(qs_1.first().pk, poa_1.application.pk)
        self.assertEqual(qs_2.first().pk, poa_2.application.pk)
        self.assertEqual(qs_3.first().pk, poa_3.application.pk)
        self.assertEqual(qs_4.first().pk, poa_2.application.pk)

    def test_filter_by_goods_related_description(self):
        application_1 = ApplicationFactory()
        good_1 = GoodFactory(
            organisation=application_1.organisation,
            description="Desc 1",
            comment="Comment 1",
            report_summary="Report Summary 1"
        )
        GoodOnApplicationFactory(application=application_1, good=good_1)
        application_2 = ApplicationFactory()
        good_2 = GoodFactory(
            organisation=application_2.organisation,
            description="afdaf",
            comment="asdfsadf",
            report_summary="asdfdsf"
        )
        GoodOnApplicationFactory(application=application_2, good=good_2)

        qs_1 = Case.objects.search(goods_related_description=good_1.description)
        qs_2 = Case.objects.search(goods_related_description=good_1.comment)
        qs_3 = Case.objects.search(goods_related_description=good_1.report_summary)

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_1.first().pk, application_1.pk)
        self.assertEqual(qs_2.first().pk, application_1.pk)
        self.assertEqual(qs_3.first().pk, application_1.pk)
