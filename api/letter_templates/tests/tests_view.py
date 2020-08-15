from rest_framework import status
from rest_framework.reverse import reverse

from api.cases.enums import AdviceType, CaseTypeReferenceEnum
from api.cases.enums import CaseTypeSubTypeEnum, CaseTypeEnum
from api.static.decisions.models import Decision
from test_helpers.clients import DataTestClient


class LetterTemplatesListTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.letter_template = self.create_letter_template(
            name="SIEL", case_types=[CaseTypeEnum.GOODS.id, CaseTypeEnum.EUA.id]
        )

    def test_get_letter_templates_success(self):
        url = reverse("letter_templates:letter_templates")

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.letter_template.id))
        self.assertEqual(response_data["name"], self.letter_template.name)
        self.assertEqual(response_data["layout"]["name"], self.letter_template.layout.name)
        case_types = [item["reference"]["key"] for item in response_data["case_types"]]
        self.assertIn(CaseTypeReferenceEnum.GQY, case_types)
        self.assertIn(CaseTypeReferenceEnum.EUA, case_types)

    def test_filter_letter_templates_success(self):
        url = reverse("letter_templates:letter_templates") + "?name=" + self.letter_template.name

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertTrue(self.letter_template.name in [template["name"] for template in response_data])
        self.assertTrue(str(self.letter_template.id) in [template["id"] for template in response_data])

    def test_get_letter_templates_for_case_success(self):
        url = reverse("letter_templates:letter_templates")
        self.letter_template.case_types.set([CaseTypeEnum.SIEL.id])
        case = self.create_standard_application_case(self.organisation)

        response = self.client.get(url + "?case=" + str(case.id), **self.gov_headers)
        response_data = response.json()["results"][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.letter_template.id))
        self.assertEqual(response_data["name"], self.letter_template.name)
        self.assertEqual(response_data["layout"]["name"], self.letter_template.layout.name)
        self.assertEqual(CaseTypeReferenceEnum.SIEL, response_data["case_types"][0]["reference"]["key"])

    def test_get_letter_templates_for_decision_success(self):
        decision = AdviceType.APPROVE
        url = reverse("letter_templates:letter_templates")
        self.letter_template.decisions.set([Decision.objects.get(name=decision)])
        self.letter_template.case_types.set([CaseTypeEnum.SIEL.id])
        case = self.create_standard_application_case(self.organisation)

        response = self.client.get(url + "?case=" + str(case.id) + "&decision=" + decision, **self.gov_headers)
        response_data = response.json()["results"][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.letter_template.id))
        self.assertEqual(response_data["name"], self.letter_template.name)
        self.assertEqual(response_data["layout"]["name"], self.letter_template.layout.name)

    def test_get_letter_templates_for_case_doesnt_show_templates_with_decisions_success(self):
        self.letter_template.case_types.set([CaseTypeEnum.SIEL.id])
        self.letter_template_with_decisions = self.create_letter_template(
            name="SIEL_2", case_types=[CaseTypeEnum.SIEL.id], decisions=[Decision.objects.get(name="approve")]
        )

        case = self.create_standard_application_case(self.organisation)

        response = self.client.get(
            reverse("letter_templates:letter_templates") + "?case=" + str(case.id), **self.gov_headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual((response.json()["results"][0]["id"]), str(self.letter_template.id))

    def test_get_letter_template_success(self):
        url = reverse("letter_templates:letter_template", kwargs={"pk": str(self.letter_template.id)})
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        template = response_data["template"]
        self.assertEqual(template["id"], str(self.letter_template.id))
        self.assertEqual(template["name"], self.letter_template.name)
        self.assertEqual(template["layout"]["id"], str(self.letter_template.layout.id))
        self.assertEqual(template["letter_paragraphs"], [str(self.letter_template.letter_paragraphs.first().id)])
        self.assertIn(CaseTypeSubTypeEnum.GOODS, str(template["case_types"]))
        self.assertIn(CaseTypeSubTypeEnum.EUA, str(template["case_types"]))
        self.assertIsNotNone(template.get("created_at"))
        self.assertIsNotNone(template.get("updated_at"))

    def test_get_letter_template_with_preview_success(self):
        url = reverse("letter_templates:letter_template", kwargs={"pk": str(self.letter_template.id)})
        url += "?generate_preview=True"

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("preview" in response_data)
        preview = response_data["preview"]
        for tag in ["<style>", "</style>"]:
            self.assertTrue(tag in preview)
        self.assertTrue(self.letter_template.letter_paragraphs.first().text in preview)

    def test_get_letter_template_with_text_success(self):
        url = reverse("letter_templates:letter_template", kwargs={"pk": str(self.letter_template.id)})
        url += "?text=True"

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("text" in response_data)
        self.assertTrue(self.letter_template.letter_paragraphs.first().text in response_data["text"])
