from django.urls import reverse
from rest_framework import status

from drafts.models import CountryOnDraft
from goodstype.models import GoodsType
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class GoodTypeCountriesManagementTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.open_draft = self.create_open_draft(self.organisation)

        self.goods_types = GoodsType.objects.filter(object_id=self.open_draft.id)
        self.goods_type_1 = self.goods_types[0]
        self.goods_type_2 = self.goods_types[1]

        # Add a country to the draft
        self.country_1 = get_country('ES')
        self.country_2 = get_country('US')
        self.country_3 = get_country('FR')

        self.all_countries = [self.country_1, self.country_2, self.country_3]
        for country in self.all_countries:
            CountryOnDraft(draft=self.open_draft, country=country).save()

        self.good_url = reverse('goodstype:goodstypes_detail', kwargs={'pk': self.goods_type_1.id})
        self.good_country_url = reverse('goodstype:assign_countries')

    def test_no_county_for_goods_type_are_returned(self):
        """
        Given a Good with no Countries assigned
        When a user requests the Good
        Then the correct Good with an empty Country list is returned
        """
        # Act
        response = self.client.get(self.good_url, **self.exporter_headers)

        # Assert
        self.assertEqual([], response.json()['good']['countries'])

    def test_all_countries_for_goods_type_are_returned(self):
        """
        Given a Good with Countries already assigned
        When a user requests the Good
        Then the correct Good with all assigned Countries are returned
        """

        # Assemble
        self.goods_type_1.countries.set(self.all_countries)

        # Act
        response = self.client.get(self.good_url, **self.exporter_headers)

        # Assert
        returned_good = response.json()['good']
        self.assertEquals(len(self.goods_type_1.countries.all()), len(returned_good['countries']))

    def test_state_can_be_over_written(self):
        """
        Given a Good with Countries already assigned
        When a user removes a good-level Country owned by their Team from the Good
        Then only that Country is removed
        """
        self.goods_type_1.countries.set(self.all_countries)
        data = {
                str(self.goods_type_1.id): [
                    self.country_1.id,
                    self.country_2.id]
        }

        self.client.put(self.good_country_url, data, **self.exporter_headers)

        self.assertEquals(2, len(self.goods_type_1.countries.all()))
        self.assertTrue(self.country_1 in self.goods_type_1.countries.all())
        self.assertTrue(self.country_2 in self.goods_type_1.countries.all())

    def test_setting_countries_on_two_goods(self):
        """
        Tests setting multiple countries on multiple goods types simultaneously
        """

        data = {
            str(self.goods_type_1.id): [
                self.country_1.id,
                self.country_2.id],
            str(self.goods_type_2.id): [
                self.country_3.id,
                self.country_1.id]
        }

        # Act
        response = self.client.put(self.good_country_url, data, **self.exporter_headers)

        # Assert
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 2)

    def test_goodstype_countries_black_box_data_persistence(self):
        data = {
            str(self.goods_type_1.id): [
                self.country_1.id,
                self.country_2.id],
            str(self.goods_type_2.id): [
                self.country_3.id,
                self.country_1.id]
        }

        # Act
        self.client.put(self.good_country_url, data, **self.exporter_headers)
        response = self.client.get(self.good_url, data, **self.exporter_headers)

        # Assert
        countries = [x.get('id') for x in response.json()['good']['countries']]
        self.assertEqual(len(countries), 2)
        self.assertIn(self.country_1.id, countries)
        self.assertIn(self.country_2.id, countries)

    def test_invalid_request_data_returns_404(self):
        """
        404 with invalid request county key
        """
        data = {
            str(self.goods_type_1.id): [
                self.country_1.id,
                self.country_2.id],
            str(self.goods_type_2.id): [
                'sdffsdfds',
                self.country_1.id]
        }

        # Act
        response = self.client.put(self.good_country_url, data, **self.exporter_headers)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
