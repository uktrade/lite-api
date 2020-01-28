from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from goods.enums import GoodControlled
from goods.models import Good
from test_helpers.clients import DataTestClient
from users.libraries.get_user import get_users_from_organisation
from users.libraries.user_to_token import user_to_token


class GoodViewTests(DataTestClient):
    def test_view_good_details(self):
        good = Good(description="thing", is_good_controlled=GoodControlled.NO, organisation=self.organisation)
        good.save()

        url = reverse("goods:good", kwargs={"pk": good.id})
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fail_view_other_organisations_goods_details(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        organisation_2_admin = get_users_from_organisation(organisation_2)[0]

        good = Good(description="thing", is_good_controlled=GoodControlled.NO, organisation=self.organisation)
        good.save()

        url = reverse("goods:good", kwargs={"pk": good.id})
        response = self.client.get(
            url,
            **{
                "HTTP_EXPORTER_USER_TOKEN": user_to_token(organisation_2_admin),
                "HTTP_ORGANISATION_ID": str(organisation_2.id),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_good__query_filter_by_description(self):
        org = self.organisation

        self.create_good("thing1", org)
        self.create_good("Thing2", org)
        self.create_good("item3", org)

        url = reverse("goods:goods") + "?description=thing"
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]
        self.assertEqual(len(response_data), 2)

        url = reverse("goods:goods") + "?description=item"
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]
        self.assertEqual(len(response_data), 1)

        url = reverse("goods:goods")
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]
        self.assertEqual(len(response_data), 3)

    def test_view_good__query_filter_by_part_number_and_combinations(self):
        org = self.organisation

        # create a set of Goods for the test
        Good.objects.create(
            description="car1",
            is_good_controlled=GoodControlled.YES,
            control_code="ML1",
            part_number="cl500",
            organisation=org,
        )

        Good.objects.create(
            description="Car2",
            is_good_controlled=GoodControlled.YES,
            control_code="ML1",
            part_number="CL300",
            organisation=org,
        )

        Good.objects.create(
            description="car3",
            is_good_controlled=GoodControlled.YES,
            control_code="ML1",
            part_number="ML500",
            organisation=org,
        )

        Good.objects.create(
            description="Truck",
            is_good_controlled=GoodControlled.YES,
            control_code="ML1",
            part_number="CL1000",
            organisation=org,
        )

        url = reverse("goods:goods") + "?part_number=cl"
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]
        self.assertEqual(len(response_data), 3)

        url = reverse("goods:goods") + "?part_number=100"
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["description"], "Truck")

        url = reverse("goods:goods") + "?part_number=cl&description=car"
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]
        self.assertEqual(len(response_data), 2)

    @parameterized.expand([("ML3", 2), ("ML3a", 1)])
    def test_view_good__query_filter_by_control_rating(self, control_rating, size):
        org = self.organisation

        self.create_good(description="thing1", org=org, control_code="ML3a")
        self.create_good(description="Thing2", org=org, control_code="ML3b")
        self.create_good(description="item3", org=org, control_code="ML4")

        url = reverse("goods:goods") + "?control_rating=" + control_rating

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), size)
