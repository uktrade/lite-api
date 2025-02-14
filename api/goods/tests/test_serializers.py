from datetime import datetime
from parameterized import parameterized

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

    @parameterized.expand(
        [
            "random good",
            "good-name",
            "good!name",
            "good-!.<>/%&*;+'(),.name",
        ]
    )
    def test_validate_good_internal_name_valid(self, name):
        serializer = GoodSerializerInternal(
            data={"name": name},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())

    @parameterized.expand(
        [
            ("", "This field may not be blank."),
            ("\r\n", "This field may not be blank."),
        ]
    )
    def test_validate_good_internal_name_invalid(self, name, error_message):
        serializer = GoodSerializerInternal(data={"name": name}, partial=True)
        self.assertFalse(serializer.is_valid())
        name_errors = serializer.errors["name"]
        self.assertEqual(len(name_errors), 1)
        self.assertEqual(
            str(name_errors[0]),
            error_message,
        )

    @parameterized.expand([None, True, False])
    def test_has_declared_at_customs(self, has_declared_at_customs):
        self.good.has_declared_at_customs = has_declared_at_customs
        serialized_data = GoodSerializerInternal(self.good).data
        self.assertEqual(serialized_data["has_declared_at_customs"], has_declared_at_customs)


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

    @parameterized.expand(
        [
            "random good",
            "good-name",
            "good!name",
            "good-!.<>/%&*;+'(),.name",
        ]
    )
    def test_validate_good_exporter_name_valid(self, address):
        serializer = GoodSerializerInternal(
            data={"address": address},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())

    @parameterized.expand(
        [
            ("", "This field may not be blank."),
            ("\r\n", "This field may not be blank."),
        ]
    )
    def test_validate_good_exporter_name_invalid(self, name, error_message):
        serializer = GoodSerializerExporterFullDetail(data={"name": name}, partial=True)
        self.assertFalse(serializer.is_valid())
        name_errors = serializer.errors["name"]
        self.assertEqual(len(name_errors), 1)
        self.assertEqual(
            str(name_errors[0]),
            error_message,
        )
