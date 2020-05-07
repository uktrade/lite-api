from django.urls import reverse
from rest_framework import status

from cases.enums import AdviceType, CaseTypeEnum
from cases.models import Advice
from test_helpers.clients import DataTestClient


class AdviceDocumentsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.advice = [AdviceType.APPROVE, AdviceType.REFUSE]
        self.create_advice(self.gov_user, self.case, "good", self.advice[0], Advice)
        self.create_advice(self.gov_user, self.case, "end_user", self.advice[1], Advice)
        self.template = self.create_letter_template(name="Template", case_types=[CaseTypeEnum.SIEL.id])
        self.url = reverse("cases:final_advice_documents", kwargs={"pk": self.case.id})

    def test_get_final_advice_no_documents(self):
        expected_format = {
            AdviceType.APPROVE: {"value": AdviceType.get_text(AdviceType.APPROVE)},
            AdviceType.REFUSE: {"value": AdviceType.get_text(AdviceType.REFUSE)},
        }

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["documents"], expected_format)

    def test_get_final_advice_with_document(self):
        document_one = self.create_generated_case_document(self.case, self.template, advice_type=self.advice[0])
        document_two = self.create_generated_case_document(self.case, self.template, advice_type=self.advice[1])

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["documents"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data[self.advice[0]]["value"], AdviceType.get_text(self.advice[0]))
        self.assertEqual(
            list(response_data[self.advice[0]]["document"].keys()), ["id", "advice_type", "user", "created_at"]
        )
        self.assertEqual(response_data[self.advice[0]]["document"]["id"], str(document_one.pk))

        self.assertEqual(response_data[self.advice[1]]["value"], AdviceType.get_text(self.advice[1]))
        self.assertEqual(
            list(response_data[self.advice[1]]["document"].keys()), ["id", "advice_type", "user", "created_at"]
        )
        self.assertEqual(response_data[self.advice[1]]["document"]["id"], str(document_two.pk))
