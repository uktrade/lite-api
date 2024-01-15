from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from api.goods.models import Good
from api.goods.tests.factories import GoodFactory
from test_helpers.clients import DataTestClient
from api.users.libraries.get_user import get_users_from_organisation
from api.users.libraries.user_to_token import user_to_token


class GoodViewTests(DataTestClient):
    def test_view_good_details(self):
        good = Good(description="thing", is_good_controlled=False, organisation=self.organisation)
        good.save()

        url = reverse("goods:good", kwargs={"pk": good.id})
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fail_view_other_organisations_goods_details(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        organisation_2_admin = get_users_from_organisation(organisation_2)[0]

        good = Good(description="thing", is_good_controlled=False, organisation=self.organisation)
        good.save()

        url = reverse("goods:good", kwargs={"pk": good.id})
        response = self.client.get(
            url,
            **{
                "HTTP_EXPORTER_USER_TOKEN": user_to_token(organisation_2_admin.baseuser_ptr),
                "HTTP_ORGANISATION_ID": str(organisation_2.id),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_good__query_filter_by_name(self):
        org = self.organisation

        GoodFactory(name="thing1", organisation=org)
        GoodFactory(name="Thing2", organisation=org)
        GoodFactory(name="item3", organisation=org)

        url = reverse("goods:goods") + "?name=thing"
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]
        self.assertEqual(len(response_data), 2)

        url = reverse("goods:goods") + "?name=item"
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
        GoodFactory(
            description="car1",
            part_number="cl500",
            organisation=self.organisation,
        )

        GoodFactory(
            description="Car2",
            part_number="CL300",
            organisation=self.organisation,
        )

        GoodFactory(
            description="car3",
            part_number="ML500",
            organisation=self.organisation,
        )

        GoodFactory(
            description="Truck",
            part_number="CL1000",
            organisation=self.organisation,
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

    @parameterized.expand([("ML", 2), ("ML1a", 2)])
    def test_view_good__query_filter_by_control_list_entry(self, control_list_entry, count):
        org = self.organisation

        GoodFactory(organisation=org, is_good_controlled=True, control_list_entries=["ML1a"])
        GoodFactory(organisation=org, is_good_controlled=True, control_list_entries=["ML1a"])

        url = reverse("goods:goods") + "?control_list_entry=" + control_list_entry

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), count)
