from difflib import SequenceMatcher

from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.reverse import reverse

from api.cases.enums import AdviceType
from api.cases.models import Case
from api.cases.tests.factories import TeamAdviceFactory, FinalAdviceFactory
from api.goodstype.tests.factories import GoodsTypeFactory
from api.staticdata.countries.factories import CountryFactory
from api.applications.enums import NSGListType
from api.applications.tests.factories import (
    PartyOnApplicationFactory,
    CountryOnApplicationFactory,
    SiteOnApplicationFactory,
    GoodOnApplicationFactory,
    StandardApplicationFactory,
    OpenApplicationFactory,
)
from api.parties.tests.factories import PartyFactory
from api.flags.tests.factories import FlagFactory
from api.goods.tests.factories import GoodFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
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
        self.assertNotEqual(site_on_application_1.site.pk, site_on_application_2.site.pk)

    def test_filter_with_organisation_name(self):
        application_1 = StandardApplicationFactory()
        application_2 = StandardApplicationFactory()

        qs_1 = Case.objects.search(organisation_name=application_1.organisation.name)
        qs_2 = Case.objects.search(organisation_name=application_2.organisation.name)

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_1.first().pk, application_1.pk)
        self.assertEqual(qs_2.first().pk, application_2.pk)

    def test_filter_with_exporter_application_reference(self):
        name_1 = "Ref 1"
        name_2 = "Ref 2"
        application_1 = StandardApplicationFactory(name=name_1)
        application_2 = StandardApplicationFactory(name=name_2)

        qs_1 = Case.objects.search(exporter_application_reference=name_1)
        qs_2 = Case.objects.search(exporter_application_reference=name_2)
        qs_3 = Case.objects.search(exporter_application_reference="Ref")

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 2)

        self.assertEqual(qs_1.first().pk, application_1.pk)
        self.assertEqual(qs_2.first().pk, application_2.pk)

    def test_filter_with_case_reference_code(self):
        application_1 = StandardApplicationFactory()
        application_2 = StandardApplicationFactory()

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
        match = SequenceMatcher(None, application_1.reference_code, application_2.reference_code).find_longest_match(
            0, len(application_1.reference_code), 0, len(application_2.reference_code)
        )

        qs_5 = Case.objects.search(case_reference=application_1.reference_code[match.a : match.a + match.size])

        self.assertEqual(qs_5.count(), 2)

    def test_filter_by_good_control_list_entry(self):
        application_1 = StandardApplicationFactory()
        good = GoodFactory(
            organisation=application_1.organisation,
            is_good_controlled=True,
            control_list_entries=["ML1a"],
        )
        GoodOnApplicationFactory(application=application_1, good=good)

        application_2 = OpenApplicationFactory()
        GoodsTypeFactory(application=application_2, is_good_controlled=True, control_list_entries=["ML2a"])

        qs_1 = Case.objects.search(control_list_entry="")
        qs_2 = Case.objects.search(control_list_entry="ML1b")
        qs_3 = Case.objects.search(control_list_entry="ML1a")
        qs_4 = Case.objects.search(control_list_entry="ML2a")

        self.assertEqual(qs_1.count(), 2)
        self.assertEqual(qs_2.count(), 0)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_4.count(), 1)

    def test_filter_by_good_regimes(self):
        application_1 = StandardApplicationFactory()
        good = GoodFactory(organisation=application_1.organisation, is_good_controlled=True)
        GoodOnApplicationFactory(application=application_1, good=good, regime_entries=["T1"])

        T1 = RegimeEntry.objects.get(name="T1")
        T5 = RegimeEntry.objects.get(name="T5")
        qs_1 = Case.objects.search(regime_entry="")
        qs_2 = Case.objects.search(regime_entry=T5.id)
        qs_3 = Case.objects.search(regime_entry=T1.id)

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 0)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_3.first().pk, application_1.pk)

    def test_filter_by_flags(self):
        flag_1 = FlagFactory(name="Name_1", level="Destination", team=self.gov_user.team, priority=9)
        flag_2 = FlagFactory(name="Name_2", level="Destination", team=self.gov_user.team, priority=10)
        flag_3 = FlagFactory(name="Name_3", level="good", team=self.gov_user.team, priority=1)
        application_1 = StandardApplicationFactory()
        application_1.flags.add(flag_1)
        application_2 = StandardApplicationFactory()
        application_2.flags.add(flag_2)
        application_3 = StandardApplicationFactory()
        application_3.flags.add(flag_2)
        application_4 = StandardApplicationFactory()
        GoodOnApplicationFactory(
            good=GoodFactory(organisation=application_4.organisation, flags=[flag_3]),
            application=application_4,
        )

        qs_1 = Case.objects.search(flags=[flag_1.id])
        qs_2 = Case.objects.search(flags=[flag_2.id])
        qs_3 = Case.objects.search(flags=[flag_3.id])

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 2)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_3.first().pk, application_4.pk)

    def test_filter_by_country(self):
        """
        What qualifies as a country on a case?
        """
        country_1 = CountryFactory(id="GB")
        country_2 = CountryFactory(id="SP")
        country_on_application = CountryOnApplicationFactory(country=country_1)
        country_on_application = CountryOnApplicationFactory(
            application=country_on_application.application, country=country_1
        )
        party_on_application = PartyOnApplicationFactory(party=PartyFactory(country=country_2))

        qs_1 = Case.objects.search(country=country_1)
        qs_2 = Case.objects.search(country=country_2)

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_1.first().pk, country_on_application.application.pk)
        self.assertEqual(qs_2.first().pk, party_on_application.application.pk)

    def test_filter_by_team_advice(self):
        application = StandardApplicationFactory()
        good = GoodFactory(organisation=application.organisation)
        TeamAdviceFactory(user=self.gov_user, team=self.team, case=application, good=good, type=AdviceType.APPROVE)

        qs_1 = Case.objects.search(team_advice_type=AdviceType.CONFLICTING)
        qs_2 = Case.objects.search(team_advice_type=AdviceType.APPROVE)

        self.assertEqual(qs_1.count(), 0)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_2.first().pk, application.pk)

    def test_filter_by_final_advice(self):
        application = StandardApplicationFactory()
        good = GoodFactory(organisation=application.organisation)
        FinalAdviceFactory(user=self.gov_user, team=self.team, case=application, good=good, type=AdviceType.APPROVE)

        qs_1 = Case.objects.search(final_advice_type=AdviceType.CONFLICTING)
        qs_2 = Case.objects.search(final_advice_type=AdviceType.APPROVE)

        self.assertEqual(qs_1.count(), 0)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_2.first().pk, application.pk)

    def test_filter_by_finalised_date_range(self):
        day_1 = timezone.datetime(day=10, month=10, year=2020)
        day_2 = timezone.datetime(day=11, month=10, year=2020)
        day_3 = timezone.datetime(day=12, month=10, year=2020)
        day_4 = timezone.datetime(day=13, month=10, year=2020)
        day_5 = timezone.datetime(day=14, month=10, year=2020)

        application_1 = StandardApplicationFactory()
        application_1.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        application_1.save()
        good = GoodFactory(organisation=application_1.organisation)
        FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=application_1, good=good, type=AdviceType.APPROVE, created_at=day_2
        )

        application_2 = StandardApplicationFactory()
        application_2.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        application_2.save()
        good = GoodFactory(organisation=application_2.organisation)
        FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=application_2, good=good, type=AdviceType.APPROVE, created_at=day_4
        )

        qs_1 = Case.objects.search(finalised_from=day_1, finalised_to=day_3)
        qs_2 = Case.objects.search(finalised_from=day_3, finalised_to=day_5)
        qs_3 = Case.objects.search(finalised_from=day_1)
        qs_4 = Case.objects.search(finalised_to=day_5)
        qs_5 = Case.objects.search(finalised_to=day_1)
        qs_6 = Case.objects.search(finalised_from=day_5)

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 2)
        self.assertEqual(qs_4.count(), 2)
        self.assertEqual(qs_5.count(), 0)
        self.assertEqual(qs_6.count(), 0)
        self.assertEqual(qs_1.first().pk, application_1.pk)
        self.assertEqual(qs_2.first().pk, application_2.pk)

    def test_filter_sla_days_range(self):
        application_1 = StandardApplicationFactory(sla_remaining_days=1)
        application_2 = StandardApplicationFactory(sla_remaining_days=3)
        application_3 = StandardApplicationFactory(sla_remaining_days=5)

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

        application_1 = StandardApplicationFactory(submitted_at=day_2)
        application_2 = StandardApplicationFactory(submitted_at=day_4)
        application_3 = StandardApplicationFactory(submitted_at=day_6)

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

        application_1 = StandardApplicationFactory(submitted_at=day_2)
        application_2 = StandardApplicationFactory(submitted_at=day_4)
        application_3 = StandardApplicationFactory(submitted_at=day_6)

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
        qs_4 = Case.objects.search(party_address=poa_2.party.address[0 : int(len(poa_2.party.address) / 2)])

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_4.count(), 1)
        self.assertEqual(qs_1.first().pk, poa_1.application.pk)
        self.assertEqual(qs_2.first().pk, poa_2.application.pk)
        self.assertEqual(qs_3.first().pk, poa_3.application.pk)
        self.assertEqual(qs_4.first().pk, poa_2.application.pk)

    def test_filter_by_goods_related_description(self):
        application_1 = StandardApplicationFactory()
        good_1 = GoodFactory(
            organisation=application_1.organisation,
            description="Desc 1",
            comment="Comment 1",
            report_summary="Report Summary 1",
        )
        GoodOnApplicationFactory(application=application_1, good=good_1)
        application_2 = StandardApplicationFactory()
        good_2 = GoodFactory(
            organisation=application_2.organisation, description="afdaf", comment="asdfsadf", report_summary="asdfdsf"
        )
        GoodOnApplicationFactory(application=application_2, good=good_2)

        application_3 = StandardApplicationFactory()
        goods_type = GoodsTypeFactory(application=application_3)

        qs_1 = Case.objects.search(goods_related_description=good_1.description)
        qs_2 = Case.objects.search(goods_related_description=good_1.comment)
        qs_3 = Case.objects.search(goods_related_description=good_1.report_summary)
        qs_4 = Case.objects.search(goods_related_description=goods_type.description)

        self.assertEqual(qs_1.count(), 1)
        self.assertEqual(qs_2.count(), 1)
        self.assertEqual(qs_3.count(), 1)
        self.assertEqual(qs_4.count(), 1)
        self.assertEqual(qs_1.first().pk, application_1.pk)
        self.assertEqual(qs_2.first().pk, application_1.pk)
        self.assertEqual(qs_3.first().pk, application_1.pk)
        self.assertEqual(qs_4.first().pk, application_3.pk)

    def test_view_flag_filter(self):
        flag_1 = FlagFactory(name="Name_1", level="Destination", team=self.gov_user.team, priority=9)
        flag_2 = FlagFactory(name="Name_2", level="Destination", team=self.gov_user.team, priority=10)

        application_1 = StandardApplicationFactory(submitted_at=timezone.now())
        application_1.flags.add(flag_1)
        application_2 = StandardApplicationFactory(submitted_at=timezone.now())
        application_2.flags.add(flag_2)

        url = reverse("cases:search")
        url_1 = f"{url}?flags={flag_1.id}"
        url_2 = f"{url}?flags={flag_2.id}"
        url_3 = f"{url}?flags={flag_1.id}&flags={flag_2.id}"

        response_1 = self.client.get(url_1, **self.gov_headers)
        response_2 = self.client.get(url_2, **self.gov_headers)
        response_3 = self.client.get(url_3, **self.gov_headers)

        data_1 = response_1.json()
        data_2 = response_2.json()
        data_3 = response_3.json()

        self.assertEqual(data_1["count"], 1)
        self.assertEqual(data_2["count"], 1)
        self.assertEqual(data_3["count"], 2)
        self.assertEqual(data_1["results"]["cases"][0]["id"], str(application_1.id))
        self.assertEqual(data_2["results"]["cases"][0]["id"], str(application_2.id))

    def test_filter_is_nca_applicable(self):
        application_1 = StandardApplicationFactory()
        application_2 = StandardApplicationFactory()
        application_3 = StandardApplicationFactory()
        good_1 = GoodFactory(
            organisation=application_1.organisation,
            description="Desc 1",
            comment="Comment 1",
            report_summary="Report Summary 1",
        )
        GoodOnApplicationFactory(application=application_1, good=good_1, is_nca_applicable=True)
        GoodOnApplicationFactory(application=application_2, good=good_1, is_nca_applicable=False)
        GoodOnApplicationFactory(application=application_2, good=good_1)

        qs_1 = Case.objects.search(is_nca_applicable="True")
        qs_2 = Case.objects.search()
        self.assertIn(application_1.pk, qs_1.values_list("id", flat=True))
        for application_id in [application_1.pk, application_2.pk, application_3.pk]:
            self.assertIn(application_id, qs_2.values_list("id", flat=True))

    def test_filter_is_trigger_list(self):
        application_1 = StandardApplicationFactory()
        application_2 = StandardApplicationFactory()
        application_3 = StandardApplicationFactory()
        good_1 = GoodFactory(
            organisation=application_1.organisation,
            description="Desc 1",
            comment="Comment 1",
            report_summary="Report Summary 1",
        )
        good_2 = GoodFactory(
            organisation=application_1.organisation,
            description="Desc 2",
            comment="Comment 2",
            report_summary="Report Summary 2",
        )
        good_3 = GoodFactory(
            organisation=application_1.organisation,
            description="Desc 3",
            comment="Comment 3",
            report_summary="Report Summary 3",
        )
        GoodOnApplicationFactory(application=application_1, good=good_1, nsg_list_type=NSGListType.TRIGGER_LIST)
        GoodOnApplicationFactory(application=application_1, good=good_2, nsg_list_type=NSGListType.DUAL_USE)
        GoodOnApplicationFactory(application=application_1, good=good_3)
        GoodOnApplicationFactory(application=application_2, good=good_1, nsg_list_type=NSGListType.DUAL_USE)
        GoodOnApplicationFactory(application=application_3, good=good_1)

        qs_1 = Case.objects.search(is_trigger_list="True")
        qs_2 = Case.objects.search()

        self.assertQuerysetEqual(qs_1, [application_1.get_case()])
        self.assertQuerysetEqual(
            qs_2, [application_1.get_case(), application_2.get_case(), application_3.get_case()], ordered=False
        )
