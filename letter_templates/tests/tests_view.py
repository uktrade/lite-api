from rest_framework import status
from rest_framework.reverse import reverse

from cases.enums import AdviceType
from cases.enums import CaseTypeSubTypeEnum, CaseTypeEnum
from picklists.enums import PickListStatus, PicklistType
from static.decisions.models import Decision
from test_helpers.clients import DataTestClient


class LetterTemplatesListTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.letter_template = self.create_letter_template(name="SIEL")
        self.letter_template.case_types.set([CaseTypeEnum.GOODS.id, CaseTypeEnum.EUA.id])

    def test_get_letter_templates_success(self):
        url = reverse("letter_templates:letter_templates")

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.letter_template.id))
        self.assertEqual(response_data["name"], self.letter_template.name)
        self.assertEqual(response_data["layout"]["id"], str(self.letter_template.layout.id))
        self.assertEqual(response_data["letter_paragraphs"], [str(self.letter_template.letter_paragraphs.first().id)])
        self.assertIn(CaseTypeSubTypeEnum.GOODS, str(response_data["case_types"]))
        self.assertIn(CaseTypeSubTypeEnum.EUA, str(response_data["case_types"]))
        self.assertIsNotNone(response_data.get("created_at"))
        self.assertIsNotNone(response_data.get("updated_at"))

    def test_get_letter_templates_for_case_success(self):
        url = reverse("letter_templates:letter_templates")
        self.letter_template.case_types.set([CaseTypeEnum.SIEL.id])
        case = self.create_standard_application_case(self.organisation)

        response = self.client.get(url + "?case=" + str(case.id), **self.gov_headers)
        response_data = response.json()["results"][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.letter_template.id))
        self.assertEqual(response_data["name"], self.letter_template.name)
        self.assertEqual(response_data["layout"]["id"], str(self.letter_template.layout.id))
        self.assertEqual(response_data["letter_paragraphs"], [str(self.letter_template.letter_paragraphs.first().id)])
        self.assertIn(str(CaseTypeEnum.SIEL.id), str(response_data["case_types"]))
        self.assertIsNotNone(response_data.get("created_at"))
        self.assertIsNotNone(response_data.get("updated_at"))

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
        self.assertEqual(response_data["layout"]["id"], str(self.letter_template.layout.id))
        self.assertEqual(response_data["letter_paragraphs"], [str(self.letter_template.letter_paragraphs.first().id)])

    def test_get_letter_templates_for_case_doesnt_show_templates_with_decisions_success(self):
        self.letter_template.case_types.set([CaseTypeEnum.SIEL.id])

        self.letter_template_with_decisions = self.create_letter_template(name="SIEL_2")
        self.letter_template_with_decisions.case_types.set([CaseTypeEnum.SIEL.id])
        self.letter_template_with_decisions.decisions.set([Decision.objects.get(name="approve")])
        self.letter_template_with_decisions.save()
        self.letter_template_with_decisions.letter_paragraphs.add(self.picklist_item)

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
        self.assertTrue(self.picklist_item.text in preview)

    def test_get_letter_template_with_text_success(self):
        url = reverse("letter_templates:letter_template", kwargs={"pk": str(self.letter_template.id)})
        url += "?text=True"

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("text" in response_data)
        self.assertTrue(self.picklist_item.text in response_data["text"])
