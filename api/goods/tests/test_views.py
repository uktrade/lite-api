from itertools import zip_longest

from django.utils.http import urlencode
from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from api.goods.enums import GoodStatus, ItemCategory
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

    @parameterized.expand(
        [
            # with the status changes in creation order
            ((),),
            ((True, False, True),),
            ((True, False, False, True, False),),
            ((True, False, False, True, True, True, False),),
        ]
    )
    def test_view_good_archive_history(self, good_archive_status):
        good = GoodFactory(organisation=self.organisation, item_category=ItemCategory.GROUP1_COMPONENTS)
        edit_url = reverse("goods:good", kwargs={"pk": str(good.id)})

        # Create sample version history
        for is_archived in good_archive_status:
            response = self.client.put(edit_url, {"is_archived": is_archived}, **self.exporter_headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # ensure correct number of revisions are created
        self.assertEqual(Version.objects.get_for_object(good).count(), len(good_archive_status))

        # determine expected statuses which should not include duplicates
        expected_archive_statuses = []
        for current, next in zip_longest(good_archive_status, good_archive_status[1:], fillvalue=None):
            if current != next:
                expected_archive_statuses.append(current)

        # reverse to get the most recent first
        expected_archive_statuses = list(reversed(expected_archive_statuses))

        url = reverse("goods:good", kwargs={"pk": good.id})
        url = f"{url}?{urlencode({'full_detail': True})}"

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        archive_history = response["good"]["archive_history"]
        actual_archive_statuses = [item["is_archived"] for item in archive_history]

        self.assertEqual(actual_archive_statuses, expected_archive_statuses)

    def test_goods_list_doesnot_excludes_archived_goods(self):
        all_goods = [GoodFactory(organisation=self.organisation, status=GoodStatus.SUBMITTED) for _ in range(5)]

        # check we can retrieve all goods
        goods_list_url = reverse("goods:goods")
        response = self.client.get(goods_list_url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        self.assertEqual(response["count"], 5)

        # archive one good
        good = all_goods[-1]
        edit_url = reverse("goods:good", kwargs={"pk": str(good.id)})
        response = self.client.put(edit_url, {"is_archived": True}, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # check archive good is not excluded
        response = self.client.get(goods_list_url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        self.assertEqual(response["count"], 5)
        active_good_ids = [item["id"] for item in response["results"]]
        self.assertIn(str(good.id), active_good_ids)

    def test_archived_goods_list(self):
        archived_goods = [
            GoodFactory(organisation=self.organisation, status=GoodStatus.SUBMITTED, is_archived=True) for _ in range(5)
        ]

        archived_goods_url = reverse("goods:archived_goods")
        response = self.client.get(archived_goods_url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        self.assertEqual(response["count"], len(archived_goods))
        expected_goods_ids = sorted([str(item.id) for item in archived_goods])
        actual_goods_ids = sorted([item["id"] for item in response["results"]])
        self.assertEqual(expected_goods_ids, actual_goods_ids)

    @parameterized.expand([("ML", 2), ("FR", 1)])
    def test_view_archived_goods_filter_by_control_list_entry(self, control_list_entry, count):
        GoodFactory(
            organisation=self.organisation,
            status=GoodStatus.SUBMITTED,
            is_archived=True,
            is_good_controlled=True,
            control_list_entries=["ML4a"],
        )
        GoodFactory(
            organisation=self.organisation,
            status=GoodStatus.SUBMITTED,
            is_archived=True,
            is_good_controlled=True,
            control_list_entries=["ML1a", "FR AI"],
        )

        url = reverse("goods:archived_goods") + "?control_list_entry=" + control_list_entry

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), count)
