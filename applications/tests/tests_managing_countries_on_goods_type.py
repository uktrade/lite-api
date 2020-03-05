from django.urls import reverse
from rest_framework import status

from applications.models import CountryOnApplication
from goodstype.models import GoodsType
from static.countries.helpers import get_country
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class GoodTypeCountriesManagementTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.open_draft = self.create_draft_open_application(self.organisation)

        self.goods_types = GoodsType.objects.filter(application=self.open_draft).order_by("id")

        self.goods_type_1 = self.goods_types[0]
        self.goods_type_2 = self.goods_types[1]

        # Add a country to the draft
        self.country_1 = get_country("ES")
        self.country_2 = get_country("US")
        self.country_3 = get_country("FR")

        self.all_countries = [self.country_1, self.country_2, self.country_3]
        for country in self.all_countries:
            CountryOnApplication(application=self.open_draft, country=country).save()

        self.good_url = reverse(
            "applications:application_goodstype",
            kwargs={"pk": self.open_draft.id, "goodstype_pk": self.goods_type_1.id},
        )
        self.good_country_url = reverse(
            "applications:application_goodstype_assign_countries", kwargs={"pk": self.open_draft.id},
        )

    def test_all_countries_are_returned_for_goods_type(self):
        """
        Given a Good with no Countries assigned
        When a user requests the Good
        Then the correct Good with all countries assigned to the application is returned
        """
        response = self.client.get(self.good_url, **self.exporter_headers)

        self.assertEqual(len(response.json()["good"]["countries"]), self.open_draft.application_countries.count())

    def test_all_countries_for_goods_type_are_returned(self):
        """
        Given a Good with Countries already assigned
        When a user requests the Good
        Then the correct Good with all assigned Countries are returned
        """
        self.goods_type_1.countries.set(self.all_countries)

        response = self.client.get(self.good_url, **self.exporter_headers)

        returned_good = response.json()["good"]
        self.assertEquals(len(self.goods_type_1.countries.all()), len(returned_good["countries"]))

    def test_state_can_be_over_written(self):
        """
        Given a Good with Countries already assigned
        When a user removes a good-level Country owned by their Team from the Good
        Then only that Country is removed
        """
        self.goods_type_1.countries.set(self.all_countries)
        data = {str(self.goods_type_1.id): [self.country_1.id, self.country_2.id]}

        self.client.put(self.good_country_url, data, **self.exporter_headers)

        self.assertEquals(2, len(self.goods_type_1.countries.all()))
        self.assertTrue(self.country_1 in self.goods_type_1.countries.all())
        self.assertTrue(self.country_2 in self.goods_type_1.countries.all())

    def test_cannot_set_no_countries_on_good(self):
        """
        Tests that a user cannot set no countries on a good
        """
        data = {
            str(self.goods_type_1.id): [],
            str(self.goods_type_2.id): [self.country_3.id, self.country_1.id],
        }

        response = self.client.put(self.good_country_url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_setting_countries_on_two_goods(self):
        """
        Tests setting multiple countries on multiple goods types simultaneously
        """

        data = {
            str(self.goods_type_1.id): [self.country_1.id, self.country_2.id],
            str(self.goods_type_2.id): [self.country_3.id, self.country_1.id],
        }

        response = self.client.put(self.good_country_url, data, **self.exporter_headers)

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 2)

    def test_goodstype_countries_black_box_data_persistence(self):
        data = {
            str(self.goods_type_1.id): [self.country_1.id, self.country_2.id],
            str(self.goods_type_2.id): [self.country_3.id, self.country_1.id],
        }

        self.client.put(self.good_country_url, data, **self.exporter_headers)
        response = self.client.get(self.good_url, data, **self.exporter_headers)

        countries = [x.get("id") for x in response.json()["good"]["countries"]]
        self.assertEqual(len(countries), 2)
        self.assertIn(self.country_1.id, countries)
        self.assertIn(self.country_2.id, countries)

    def test_invalid_request_data_returns_404(self):
        """
        404 with invalid request country key
        """
        data = {
            str(self.goods_type_1.id): [self.country_1.id, self.country_2.id],
            str(self.goods_type_2.id): ["sdffsdfds", self.country_1.id],
        }

        response = self.client.put(self.good_country_url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_audit_entries_are_created(self):
        """
        Given a Good with Countries already assigned
        When a user assigns a new country to the good and removes the existing one
        Then two audit entries should be made showing the addition and removal
        """
        case = self.submit_application(self.open_draft)
        case.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        case.save()

        self.goods_type_1.countries.set([self.country_1])
        data = {str(self.goods_type_1.id): [self.country_2.id]}

        self.client.put(self.good_country_url, data, **self.exporter_headers)

        response_data = self.client.get(reverse("cases:activity", kwargs={"pk": case.id}), **self.gov_headers).json()

        self.assertEqual(len(response_data["activity"]), 2)
        self.assertIn("added the destinations United States to 'thing'", str(response_data))
        self.assertIn("removed the destinations Spain from 'thing'", str(response_data))
