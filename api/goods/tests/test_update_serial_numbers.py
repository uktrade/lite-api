from parameterized import parameterized

from django.urls import reverse

from test_helpers.clients import DataTestClient

from api.goods.enums import GoodStatus


class GoodUpdateSerialNumbers(DataTestClient):
    def setUp(self):
        super().setUp()

        self.good = self.create_good(
            create_firearm_details=True,
            description="This is a good",
            organisation=self.organisation,
        )
        self.good.status = GoodStatus.SUBMITTED
        self.good.save()

        self.good.firearm_details.serial_numbers = []
        self.good.firearm_details.save()

        self.url = reverse("goods:update_serial_numbers", kwargs={"pk": self.good.pk})

    def test_update_serial_numbers(self):
        serial_numbers = ["11111", "22222", "33333"]
        response = self.client.put(
            self.url,
            {
                "serial_numbers": serial_numbers,
            },
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"serial_numbers": serial_numbers},
        )

        self.good.refresh_from_db()
        self.assertEqual(
            self.good.firearm_details.serial_numbers,
            serial_numbers,
        )

    @parameterized.expand([GoodStatus.DRAFT, GoodStatus.QUERY, GoodStatus.VERIFIED])
    def test_invalid_good_statuses(self, status):
        self.good.status = status
        self.good.save()

        serial_numbers = ["11111", "22222", "33333"]
        response = self.client.put(
            self.url,
            {
                "serial_numbers": serial_numbers,
            },
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, 400)

        self.good.refresh_from_db()
        self.assertEqual(
            self.good.firearm_details.serial_numbers,
            [],
        )

    def test_update_serial_numbers_invalid_data(self):
        serial_numbers = "notvaliddata"
        response = self.client.put(
            self.url,
            {
                "serial_numbers": serial_numbers,
            },
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"errors": {"serial_numbers": ['Expected a list of items but got type "str".']}},
        )

        self.good.refresh_from_db()
        self.assertEqual(
            self.good.firearm_details.serial_numbers,
            [],
        )
