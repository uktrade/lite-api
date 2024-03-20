import uuid

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.audit_trail.models import Audit
from api.goods.tests.factories import GoodFactory
from api.staticdata.units.enums import Units
from test_helpers.clients import DataTestClient
from test_helpers.decorators import none_param_tester


class AddingGoodsOnApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_standard_application(self.organisation)
        self.good = GoodFactory(name="A good", organisation=self.organisation)

    def test_add_a_good_to_a_draft(self):
        self.create_good_document(
            self.good,
            user=self.exporter_user,
            organisation=self.organisation,
            name="doc1",
            s3_key="doc3",
        )

        data = {
            "good_id": self.good.id,
            "quantity": 1200.098896,
            "unit": Units.NAR,
            "value": 50000.45,
            "is_good_incorporated": True,
        }

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()
        audit_qs = Audit.objects.all()

        # The standard draft comes with one good pre-added, plus the good added in this test makes 2
        self.assertEqual(len(response_data["goods"]), 2)
        # No audit created for drafts.
        self.assertEqual(audit_qs.count(), 0)

    def test_user_cannot_add_another_organisations_good_to_a_draft(self):
        good_name = "A good"
        organisation_2, _ = self.create_organisation_with_exporter_user()
        good = GoodFactory(name=good_name, organisation=organisation_2)
        self.create_good_document(
            good,
            user=self.exporter_user,
            organisation=self.organisation,
            name="doc1",
            s3_key="doc3",
        )
        data = {"good_id": good.id, "quantity": 1200, "unit": Units.KGM, "value": 50000}
        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()
        audit_qs = Audit.objects.all()

        # The good that came with the pre-created standard draft remains the only good on the draft
        self.assertEqual(len(response_data["goods"]), 1)
        self.assertEqual(audit_qs.count(), 0)

    @parameterized.expand(
        [
            [
                {
                    "value": "123.45",
                    "quantity": "1123423.901234",
                    "response": status.HTTP_201_CREATED,
                }
            ],
            [
                {
                    "value": "123.45",
                    "quantity": "1234.12341341",
                    "response": status.HTTP_400_BAD_REQUEST,
                }
            ],
            [
                {
                    "value": "2123.45",
                    "quantity": "1234",
                    "response": status.HTTP_201_CREATED,
                }
            ],
            [
                {
                    "value": "123.4523",
                    "quantity": "1234",
                    "response": status.HTTP_400_BAD_REQUEST,
                }
            ],
        ]
    )
    def test_adding_goods_with_different_number_formats(self, data):
        self.create_good_document(
            self.good,
            user=self.exporter_user,
            organisation=self.organisation,
            name="doc1",
            s3_key="doc3",
        )

        post_data = {
            "good_id": self.good.id,
            "quantity": data["quantity"],
            "unit": Units.NAR,
            "value": data["value"],
            "is_good_incorporated": True,
        }

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.post(url, post_data, **self.exporter_headers)

        self.assertEqual(response.status_code, data["response"])

    def test_add_a_good_to_a_submitted_application_failure(self):
        application = self.create_draft_standard_application(self.organisation)
        self.submit_application(application)
        self.create_good_document(
            self.good,
            user=self.exporter_user,
            organisation=self.organisation,
            name="doc1",
            s3_key="doc3",
        )
        data = {
            "good_id": self.good.id,
            "quantity": 1200.098896,
            "unit": Units.NAR,
            "value": 50000.45,
        }

        url = reverse("applications:application_goods", kwargs={"pk": application.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            [
                {
                    "value": "123.45",
                    "quantity": "1123423.901234",
                    "validate_only": True,
                    "response": status.HTTP_200_OK,
                }
            ],
            [
                {
                    "good_id": uuid.uuid4(),
                    "value": "123.45",
                    "quantity": "1123423.901234",
                    "validate_only": False,
                    "response": status.HTTP_404_NOT_FOUND,
                }
            ],
            [
                {
                    "value": "123.45",
                    "quantity": "100.00",
                    "validate_only": "Bob",
                    "response": status.HTTP_400_BAD_REQUEST,
                }
            ],
            [
                {
                    "value": "123.45",
                    "quantity": "100.00",
                    "validate_only": 1,
                    "response": status.HTTP_400_BAD_REQUEST,
                }
            ],
            [
                {
                    "value": "123.45",
                    "quantity": "asd",
                    "validate_only": True,
                    "response": status.HTTP_400_BAD_REQUEST,
                }
            ],
        ]
    )
    def test_adding_good_validate_only(self, data):
        application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:application_goods", kwargs={"pk": application.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, data["response"])

    def test_adding_good_without_document_or_reason_success(self):
        good = GoodFactory(organisation=self.organisation)
        good.is_document_available = False
        good.save()
        data = {
            "good_id": good.id,
            "quantity": 1200.098896,
            "unit": Units.NAR,
            "value": 50000.45,
            "is_good_incorporated": True,
        }

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_adding_good_with_reason_official_sensitive_success(self):
        good = GoodFactory(organisation=self.organisation)
        good.is_document_sensitive = True
        good.save()
        data = {
            "good_id": good.id,
            "quantity": 1200.098896,
            "unit": Units.NAR,
            "value": 50000.45,
            "is_good_incorporated": True,
        }

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @none_param_tester(12, Units.NAR, 50, True)
    def test_add_a_good_to_a_draft_failure(self, quantity, unit, value, is_good_incorporated):
        """
        Ensure all params have to be sent otherwise fail
        """
        self.create_draft_standard_application(self.organisation)
        GoodFactory(organisation=self.organisation)
        self.create_good_document(
            self.good,
            user=self.exporter_user,
            organisation=self.organisation,
            name="doc1",
            s3_key="doc3",
        )
        data = {
            "good_id": self.good.id,
            "quantity": quantity,
            "unit": unit,
            "value": value,
            "is_good_incorporated": is_good_incorporated,
        }

        response = self.client.post(
            reverse("applications:application_goods", kwargs={"pk": self.draft.id}), data, **self.exporter_headers
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AddingGoodsOnApplicationFirearmsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_standard_application(self.organisation)
        self.good = GoodFactory(organisation=self.organisation)

    @parameterized.expand(
        [
            (
                {
                    "quantity": 1,
                    "unit": Units.NAR,
                    "value": 1,
                    "is_good_incorporated": True,
                    "firearm_details": {
                        "year_of_manufacture": 2020,
                        "section_certificate_date_of_expiry": "2025-12-31",
                        "number_of_items": 1,
                        "serial_numbers": ["serial1"],
                    },
                },
                True,
            ),
            (
                {
                    "quantity": 1,
                    "unit": Units.NAR,
                    "value": 1,
                    "is_good_incorporated": True,
                },
                False,
            ),
        ]
    )
    def test_add_a_good_to_a_draft_with_firearms_details(self, data, firearm_details_created):
        self.create_good_document(
            self.good,
            user=self.exporter_user,
            organisation=self.organisation,
            name="doc1",
            s3_key="doc3",
        )

        data["good_id"] = self.good.id

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})

        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()
        new_good = response_data["goods"][1]
        # The standard draft good has a yom of 1992 make sure it has been
        # updated to 2020 on firearms details on application
        self.assertEqual(firearm_details_created, bool(new_good["firearm_details"]))
        if firearm_details_created:
            self.assertNotEqual(
                self.good.firearm_details.year_of_manufacture, new_good["firearm_details"]["year_of_manufacture"]
            )
            self.assertEqual(
                new_good["firearm_details"]["year_of_manufacture"], data["firearm_details"]["year_of_manufacture"]
            )

    @parameterized.expand(
        [
            ("No",),
            ("Unsure",),
            ("",),
        ],
    )
    def test_add_a_good_to_a_draft_with_firearms_details_is_covered_by_section_5_values(
        self, covered_by_firearms_act_negative_value
    ):
        self.create_good_document(
            self.good,
            user=self.exporter_user,
            organisation=self.organisation,
            name="doc1",
            s3_key="doc3",
        )

        data = {
            "good_id": self.good.id,
            "quantity": 1,
            "unit": Units.NAR,
            "value": 1,
            "is_good_incorporated": True,
            "firearm_details": {
                "year_of_manufacture": 2020,
                "number_of_items": 1,
                "serial_numbers": ["serial1"],
                "is_covered_by_firearm_act_section_one_two_or_five": covered_by_firearms_act_negative_value,
            },
        }

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})

        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
