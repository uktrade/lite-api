from django.utils import timezone

from api.applications.tests.factories import (
    GoodOnApplicationFactory,
    StandardApplicationFactory,
)
from api.staticdata.countries.factories import CountryFactory
from api.parties.tests.factories import PartyFactory
from test_helpers.clients import DataTestClient

from api.applications.tests.factories import PartyOnApplicationFactory

from api.goods.tests.factories import GoodFactory
from api.goods.serializers import GoodOnApplicationSerializer, GoodSerializerInternal
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject


class GoodOnApplicationSerializerTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.application = StandardApplicationFactory.create()
        good = GoodFactory.create(organisation=self.organisation)

        self.a_good_on_application = GoodOnApplicationFactory.create(
            application=self.application,
            good=good,
        )
        self.b_good_on_application = GoodOnApplicationFactory.create(
            application=self.application,
            good=good,
        )

    def test_get_destinations(self):
        self.assertEqual(
            GoodOnApplicationSerializer().get_destinations(self.a_good_on_application),
            [],
        )
        self.assertEqual(
            GoodOnApplicationSerializer().get_destinations(self.b_good_on_application),
            [],
        )

        country = CountryFactory.create(id="NZ", name="New Zealand", type="2")
        party_on_application = PartyOnApplicationFactory.create(
            application=self.application,
            party__country=country,
        )
        self.assertEqual(
            GoodOnApplicationSerializer().get_destinations(self.a_good_on_application),
            [party_on_application.party.country.name],
        )
        self.assertEqual(
            GoodOnApplicationSerializer().get_destinations(self.b_good_on_application),
            [party_on_application.party.country.name],
        )

        another_country = CountryFactory.create(id="JP", name="Japan", type="2")
        another_party_on_application = PartyOnApplicationFactory.create(
            application=self.application,
            party__country=another_country,
        )
        self.assertNotEqual(
            party_on_application.party.country.name,
            another_party_on_application.party.country.name,
        )
        self.assertEqual(
            sorted(GoodOnApplicationSerializer().get_destinations(self.a_good_on_application)),
            sorted(
                [
                    another_party_on_application.party.country.name,
                    party_on_application.party.country.name,
                ]
            ),
        )
        self.assertEqual(
            sorted(GoodOnApplicationSerializer().get_destinations(self.b_good_on_application)),
            sorted(
                [
                    another_party_on_application.party.country.name,
                    party_on_application.party.country.name,
                ]
            ),
        )

    def test_get_destinations_excludes_deleted_party_on_application(self):
        PartyOnApplicationFactory.create(
            application=self.application,
            deleted_at=timezone.now(),
        )
        self.assertEqual(
            GoodOnApplicationSerializer().get_destinations(self.a_good_on_application),
            [],
        )
        self.assertEqual(
            GoodOnApplicationSerializer().get_destinations(self.b_good_on_application),
            [],
        )

    def test_get_destinations_distinct_values(self):
        country = CountryFactory.create()
        country.name = "Test Country"
        country.save()

        party = PartyFactory.create(country=country)

        a_party_on_application = PartyOnApplicationFactory.create(
            application=self.application,
            party=party,
        )
        b_party_on_application = PartyOnApplicationFactory.create(
            application=self.application,
            party=party,
        )
        self.assertEqual(
            a_party_on_application.party.country.name,
            b_party_on_application.party.country.name,
        )

        self.assertEqual(
            GoodOnApplicationSerializer().get_destinations(self.a_good_on_application),
            ["Test Country"],
        )
        self.assertEqual(
            GoodOnApplicationSerializer().get_destinations(self.b_good_on_application),
            ["Test Country"],
        )
