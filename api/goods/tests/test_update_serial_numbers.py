from parameterized import parameterized

from django.urls import reverse

from test_helpers.clients import DataTestClient

from api.applications.tests.factories import StandardApplicationFactory
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.goods.enums import GoodStatus
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class GoodUpdateSerialNumbers(DataTestClient):
    def setUp(self):
        super().setUp()

        self.good = self.create_good(
            create_firearm_details=True,
            description="This is a good",
            organisation=self.organisation,
        )
        self.good.status = GoodStatus.SUBMITTED
        self.good.name = "Good name"
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

    def test_update_serial_numbers_audit_logs(self):
        application_1 = StandardApplicationFactory()
        self.good.goods_on_application.create(application=application_1)

        application_2 = StandardApplicationFactory()
        self.good.goods_on_application.create(application=application_2)

        application_3 = StandardApplicationFactory()
        application_3.status = get_case_status_by_status(CaseStatusEnum.DRAFT)
        application_3.save()
        self.good.goods_on_application.create(application=application_3)

        self.assertFalse(Audit.objects.exists())

        serial_numbers = ["11111", "22222", "33333"]
        response = self.client.put(
            self.url,
            {
                "serial_numbers": serial_numbers,
            },
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, 200)

        audit_objects = Audit.objects.filter(verb=AuditType.UPDATED_SERIAL_NUMBERS)

        audit_object = audit_objects.get(target_object_id=application_1.pk)
        self.assertEqual(
            audit_object.actor,
            self.exporter_user.baseuser_ptr,
        )
        self.assertEqual(
            audit_object.payload,
            {
                "good_name": self.good.name,
            },
        )

        audit_object = audit_objects.get(target_object_id=application_2.pk)
        self.assertEqual(
            audit_object.actor,
            self.exporter_user.baseuser_ptr,
        )
        self.assertEqual(
            audit_object.payload,
            {
                "good_name": self.good.name,
            },
        )

        with self.assertRaises(Audit.DoesNotExist):
            audit_objects.get(target_object_id=application_3.pk)
