from datetime import datetime

from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status

from api.applications.tests.factories import (
    GoodOnApplicationFactory,
    StandardApplicationFactory,
)
from api.goods.enums import ItemCategory
from api.staticdata.countries.factories import CountryFactory
from api.parties.tests.factories import PartyFactory
from test_helpers.clients import DataTestClient

from api.applications.tests.factories import PartyOnApplicationFactory

from api.goods.tests.factories import GoodFactory
from api.goods.serializers import GoodSerializerExporterFullDetail, GoodOnApplicationSerializer, GoodSerializerInternal
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


class GoodSerializerInternalTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.good = GoodFactory.create(organisation=self.organisation)
        self.good.report_summary_prefix = ReportSummaryPrefix.objects.first()
        self.good.report_summary_subject = ReportSummarySubject.objects.first()

    def test_report_summary_present(self):
        serialized_data = GoodSerializerInternal(self.good).data
        actual_prefix = serialized_data["report_summary_prefix"]
        actual_subject = serialized_data["report_summary_subject"]
        self.assertEqual(actual_prefix["id"], str(self.good.report_summary_prefix.id))
        self.assertEqual(actual_prefix["name"], self.good.report_summary_prefix.name)
        self.assertEqual(actual_subject["id"], str(self.good.report_summary_subject.id))
        self.assertEqual(actual_subject["name"], self.good.report_summary_subject.name)


class GoodSerializerExporterFullDetailTests(DataTestClient):

    @freeze_time("2024-01-01 09:00:00")
    def test_exporter_has_archive_history(self):
        good = GoodFactory(organisation=self.organisation, item_category=ItemCategory.GROUP1_COMPONENTS)
        edit_url = reverse("goods:good_details", kwargs={"pk": str(good.id)})

        data = {"is_archived": True}
        response = self.client.put(edit_url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        good.refresh_from_db()

        good_details = GoodSerializerExporterFullDetail(good).data
        archive_history = good_details["archive_history"]
        self.assertEqual(len(archive_history), 1)
        archive_history = archive_history[0]
        self.assertEqual(archive_history["is_archived"], data["is_archived"])
        self.assertEqual(
            archive_history["user"],
            {
                "first_name": self.exporter_user.first_name,
                "last_name": self.exporter_user.last_name,
                "email": self.exporter_user.email,
                "pending": self.exporter_user.pending,
            },
        )
        self.assertEqual(
            archive_history["actioned_on"],
            datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.get_current_timezone()),
        )
