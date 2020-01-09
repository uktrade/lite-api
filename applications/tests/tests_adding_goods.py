import uuid

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from applications.models import GoodOnApplication
from audit_trail.models import Audit
from lite_content.lite_api import strings
from static.missing_document_reasons.enums import GoodMissingDocumentReasons
from static.units.enums import Units
from test_helpers.clients import DataTestClient


class AddingGoodsOnApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_application(self.organisation)
        self.good = self.create_controlled_good("A good", self.organisation)

    def test_add_a_good_to_a_draft(self):
        good_name = "A good"
        self.create_standard_application(self.organisation)
        self.create_controlled_good(good_name, self.organisation)

        self.create_good_document(
            self.good, user=self.exporter_user, organisation=self.organisation, name="doc1", s3_key="doc3",
        )

        data = {
            "good_id": self.good.id,
            "quantity": 1200.098896,
            "unit": Units.NAR,
            "value": 50000.45,
            "is_good_incorporated": True
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
        good = self.create_controlled_good(good_name, organisation_2)
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
            "is_good_incorporated": True
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
        good_name = "A good"
        draft = self.create_open_application(self.organisation)
        pre_test_good_count = GoodOnApplication.objects.all().count()
        self.create_controlled_good(good_name, self.organisation)
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

    def test_add_a_good_to_a_submitted_application__failure(self):
        application = self.create_standard_application(self.organisation)
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
        application = self.create_standard_application(self.organisation)
        url = reverse("applications:application_goods", kwargs={"pk": application.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, data["response"])

    def test_adding_good_without_document_or_reason_failure(self):
        data = {
            "good_id": self.good.id,
            "quantity": 1200.098896,
            "unit": Units.NAR,
            "value": 50000.45,
            "is_good_incorporated": True
        }

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"], strings.Goods.DOCUMENT_ERROR)

    def test_adding_good_with_reason_official_sensitive_success(self):
        good = self.create_controlled_good("A good", self.organisation)
        good.missing_document_reason = GoodMissingDocumentReasons.OFFICIAL_SENSITIVE
        good.save()
        data = {
            "good_id": good.id,
            "quantity": 1200.098896,
            "unit": Units.NAR,
            "value": 50000.45,
            "is_good_incorporated": True
        }

        url = reverse("applications:application_goods", kwargs={"pk": self.draft.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
