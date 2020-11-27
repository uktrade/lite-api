import uuid

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.applications.models import GoodOnApplication
from api.audit_trail.models import Audit
from api.cases.enums import CaseTypeEnum
from api.goods.enums import ItemType
from lite_content.lite_api import strings
from api.staticdata.missing_document_reasons.enums import GoodMissingDocumentReasons
from api.staticdata.units.enums import Units
from test_helpers.clients import DataTestClient
from test_helpers.decorators import none_param_tester


class AddingGoodsOnApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_standard_application(self.organisation)
        self.good = self.create_good("A good", self.organisation)

    def test_add_a_good_to_a_draft(self):
        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
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

    @parameterized.expand(
        [
            [{"value": "", "quantity": "", "expected_value": "0.00", "expected_quantity": 1.0,}],
            [{"value": 100, "quantity": 10, "expected_value": "100.00", "expected_quantity": 10.0,}],
            [{"value": "", "quantity": 5, "expected_value": "0.00", "expected_quantity": 5.0,}],
            [{"value": 123.0, "quantity": "", "expected_value": "123.00", "expected_quantity": 1.0,}],
        ]
    )
    def test_add_an_intangible_good_to_a_draft(self, data):
        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
        )

        expected_value = data["expected_value"]
        expected_quantity = data["expected_quantity"]

        data = {
            "good_id": self.good.id,
            "quantity": data["quantity"],
            "unit": Units.ITG,
            "value": data["value"],
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
        # The intangible good defaults quantity and value to 1.0 and 0.00 respectively if they aren't set
        self.assertEqual((response_data["goods"][1]["quantity"]), expected_quantity)
        self.assertEqual((response_data["goods"][1]["value"]), expected_value)
        # No audit created for drafts.
        self.assertEqual(audit_qs.count(), 0)

    def test_user_cannot_add_another_organisations_good_to_a_draft(self):
        good_name = "A good"
        organisation_2, _ = self.create_organisation_with_exporter_user()
        good = self.create_good(good_name, organisation_2)
        self.create_good_document(
            good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
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
            [{"value": "123.45", "quantity": "1123423.901234", "response": status.HTTP_201_CREATED,}],
            [{"value": "123.45", "quantity": "1234.12341341", "response": status.HTTP_400_BAD_REQUEST,}],
            [{"value": "2123.45", "quantity": "1234", "response": status.HTTP_201_CREATED,}],
            [{"value": "123.4523", "quantity": "1234", "response": status.HTTP_400_BAD_REQUEST,}],
        ]
    )
    def test_adding_goods_with_different_number_formats(self, data):
        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
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

    def test_add_a_good_to_open_application_failure(self):
        """
        Given a draft open application
        When I try to add a good to the application
        Then a 400 BAD REQUEST is returned
        And no goods have been added
        """
        draft = self.create_draft_open_application(self.organisation)
        pre_test_good_count = GoodOnApplication.objects.all().count()
        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
        )

        data = {
            "good_id": self.good.id,
            "quantity": 1200.098896,
            "unit": Units.NAR,
            "value": 50000.45,
        }
        url = reverse("applications:application_goods", kwargs={"pk": draft.id})

        response = self.client.post(url, data, **self.exporter_headers)
        audit_qs = Audit.objects.all()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(GoodOnApplication.objects.all().count(), pre_test_good_count)
        self.assertEqual(audit_qs.count(), 0)

    def test_add_a_good_to_a_submitted_application_failure(self):
        application = self.create_draft_standard_application(self.organisation)
        self.submit_application(application)
        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
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
            [{"value": "123.45", "quantity": "1123423.901234", "validate_only": True, "response": status.HTTP_200_OK,}],
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
            [{"value": "123.45", "quantity": "100.00", "validate_only": 1, "response": status.HTTP_400_BAD_REQUEST,}],
            [{"value": "123.45", "quantity": "asd", "validate_only": True, "response": status.HTTP_400_BAD_REQUEST,}],
        ]
    )
    def test_adding_good_validate_only(self, data):
        application = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:application_goods", kwargs={"pk": application.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, data["response"])

    def test_adding_good_without_document_or_reason_failure(self):
        data = {
            "good_id": self.good.id,
            "quantity": 1200.098896,
            "unit": Units.NAR,
            "value": 50000.45,
            "is_good_incorporated": True,
        }

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"], strings.Goods.DOCUMENT_ERROR)

    def test_adding_good_with_reason_official_sensitive_success(self):
        good = self.create_good("A good", self.organisation)
        good.missing_document_reason = GoodMissingDocumentReasons.OFFICIAL_SENSITIVE
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
        self.create_good("A good", self.organisation)
        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
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
        self.good = self.create_good("A good", self.organisation, create_firearm_details=True)

    @parameterized.expand(
        [
            (
                {
                    "quantity": 1,
                    "unit": Units.NAR,
                    "value": 1,
                    "is_good_incorporated": True,
                    "year_of_manufacture": 2020,
                },
                True,
            ),
            ({"quantity": 1, "unit": Units.NAR, "value": 1, "is_good_incorporated": True,}, False),
        ]
    )
    def test_add_a_good_to_a_draft_with_firearms_details(self, data, firearm_details_created):
        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
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
                int(self.good.firearm_details.year_of_manufacture), new_good["firearm_details"]["year_of_manufacture"]
            )
            self.assertEqual(new_good["firearm_details"]["year_of_manufacture"], data["year_of_manufacture"])


class AddingGoodsOnApplicationExhibitionTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.good = self.create_good("A good", self.organisation)

    def test_add_a_good_to_a_exhibition_draft_choice(self):
        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
        )

        data = {"good_id": self.good.id, "item_type": ItemType.VIDEO}

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        response_data = response.json()["good"]

        self.assertIsNone(response_data["value"])
        self.assertIsNone(response_data["quantity"])
        self.assertIsNone(response_data["unit"])
        self.assertIsNone(response_data["is_good_incorporated"])

        self.assertEqual(response_data["good"], str(self.good.id))
        self.assertEqual(response_data["item_type"], str(ItemType.VIDEO))
        # we expect other item type to be None as it should not be set unless ItemType is Other
        self.assertIsNone(response_data["other_item_type"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # check application
        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()
        audit_qs = Audit.objects.all()

        # The standard draft comes with one good pre-added, plus the good added in this test makes 2
        self.assertEqual(len(response_data["goods"]), 2)
        # No audit created for drafts.
        self.assertEqual(audit_qs.count(), 0)

    def test_add_a_good_to_a_exhibition_other(self):
        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
        )
        other_value = "abcde"
        data = {"good_id": self.good.id, "item_type": ItemType.OTHER, "other_item_type": other_value}

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        response_data = response.json()["good"]

        self.assertIsNone(response_data["value"])
        self.assertIsNone(response_data["quantity"])
        self.assertIsNone(response_data["unit"])
        self.assertIsNone(response_data["is_good_incorporated"])

        self.assertEqual(response_data["good"], str(self.good.id))
        self.assertEqual(response_data["item_type"], str(ItemType.OTHER))
        self.assertEqual(response_data["other_item_type"], other_value)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # check application
        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()
        audit_qs = Audit.objects.all()

        # The standard draft comes with one good pre-added, plus the good added in this test makes 2
        self.assertEqual(len(response_data["goods"]), 2)
        # No audit created for drafts.
        self.assertEqual(audit_qs.count(), 0)

    def test_add_a_good_to_a_exhibition_other_blank_failure(self):
        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
        )

        data = {"good_id": self.good.id, "item_type": ItemType.OTHER, "other_item_type": ""}

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        errors = response.json()["errors"]

        self.assertEqual(errors["other_item_type"][0], strings.Goods.OTHER_ITEM_TYPE)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        # Still one good as test failed
        self.assertEqual(len(response_data["goods"]), 1)

    def test_add_a_good_to_a_exhibition_no_data_failure(self):
        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
        )

        data = {"good_id": self.good.id}

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        errors = response.json()["errors"]

        self.assertEqual(errors["item_type"][0], strings.Goods.ITEM_TYPE)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        # Still one good as test failed
        self.assertEqual(len(response_data["goods"]), 1)
