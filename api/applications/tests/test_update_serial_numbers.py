from parameterized import parameterized

from django.urls import reverse

from test_helpers.clients import DataTestClient

from api.applications.tests.factories import GoodFactory, GoodOnApplicationFactory, StandardApplicationFactory
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.goods.tests.factories import FirearmFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class GoodOnApplicationUpdateSerialNumbers(DataTestClient):
    ALLOWED_STATUSES = [
        CaseStatusEnum.SUBMITTED,
        CaseStatusEnum.FINALISED,
    ]
    # DISALLOWED_STATUSES is used to parameterize tests, make the order stable to enable pytest-xdist
    DISALLOWED_STATUSES = sorted(set(CaseStatusEnum.all()) - set(ALLOWED_STATUSES))

    def setUp(self):
        super().setUp()

        self.application = StandardApplicationFactory()
        self.good = GoodFactory(
            organisation=self.application.organisation,
        )
        self.firearm_details = FirearmFactory(serial_numbers=[])
        self.good_on_application = GoodOnApplicationFactory(
            application=self.application,
            firearm_details=self.firearm_details,
            good=self.good,
        )

        self.url = reverse(
            "applications:good_on_application_update_serial_numbers",
            kwargs={
                "pk": self.application.pk,
                "good_on_application_pk": self.good_on_application.pk,
            },
        )

    @parameterized.expand(ALLOWED_STATUSES)
    def test_update_serial_numbers(self, application_status):
        self.application.status = get_case_status_by_status(application_status)
        self.application.save()

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

        self.firearm_details.refresh_from_db()
        self.assertEqual(
            self.firearm_details.serial_numbers,
            serial_numbers,
        )

    @parameterized.expand(DISALLOWED_STATUSES)
    def test_invalid_application_statuses(self, application_status):
        self.application.status = get_case_status_by_status(application_status)
        self.application.save()

        serial_numbers = ["11111", "22222", "33333"]
        response = self.client.put(
            self.url,
            {
                "serial_numbers": serial_numbers,
            },
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, 400)

        self.firearm_details.refresh_from_db()
        self.assertEqual(
            self.firearm_details.serial_numbers,
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

        self.firearm_details.refresh_from_db()
        self.assertEqual(
            self.firearm_details.serial_numbers,
            [],
        )

    def test_update_serial_numbers_audit_logs(self):
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

        audit_object = audit_objects.get(target_object_id=self.application.pk)
        self.assertEqual(audit_object.actor, self.exporter_user)
        self.assertEqual(
            audit_object.payload,
            {
                "good_name": self.good.name,
            },
        )
