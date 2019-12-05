import uuid

from rest_framework import status
from rest_framework.reverse import reverse

from cases.enums import CaseTypeEnum
from letter_templates.models import LetterTemplate
from picklists.enums import PickListStatus, PicklistType
from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient
from users.libraries.user_to_token import user_to_token


class GetGeneratedCaseDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.picklist_item = self.create_picklist_item(
            "#1", self.team, PicklistType.LETTER_PARAGRAPH, PickListStatus.ACTIVE
        )
        self.letter_layout = LetterLayout.objects.first()
        self.letter_template = LetterTemplate.objects.create(name="SIEL", layout=self.letter_layout,)
        self.letter_template.case_types.add(CaseTypeEnum.APPLICATION)
        self.letter_template.letter_paragraphs.add(self.picklist_item)
        self.case = self.create_standard_application_case(self.organisation)
        self.generated_case_document = self.create_generated_case_document(self.case, template=self.letter_template)

    def test_get_generated_documents_success(self):
        url = reverse("applications:application_generated_documents", kwargs={"pk": str(self.case.pk)})

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["generated_documents"]), 1)

    def test_get_generated_documents_returns_empty_list_when_no_documents_have_been_generated_success(self):
        self.generated_case_document.delete()
        url = reverse("applications:application_generated_documents", kwargs={"pk": str(self.case.pk)})

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["generated_documents"], [])

    def test_get_generated_documents_as_unauthorised_exporter_user_failure(self):
        organisation, exporter_user = self.create_organisation_with_exporter_user()
        exporter_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(exporter_user),
            "HTTP_ORGANISATION_ID": organisation.id,
        }
        url = reverse("applications:application_generated_documents", kwargs={"pk": str(self.case.pk)})

        response = self.client.get(url, **exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_generated_documents_as_gov_user_failure(self):
        url = reverse("applications:application_generated_documents", kwargs={"pk": str(self.case.pk)})

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_generated_document_success(self):
        url = reverse(
            "applications:application_generated_document",
            kwargs={"pk": str(self.case.pk), "gcd_pk": str(self.generated_case_document.pk)},
        )

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        document = response.json()["document"]
        self.assertEqual(document["name"], self.generated_case_document.name)

    def test_get_generated_document_when_document_doesnt_exist_failure(self):
        url = reverse(
            "applications:application_generated_document",
            kwargs={"pk": str(self.case.pk), "gcd_pk": str(uuid.uuid4())},
        )

        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["document"], None)

    def test_get_generated_document_as_unauthorised_exporter_user_failure(self):
        organisation, exporter_user = self.create_organisation_with_exporter_user()
        exporter_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(exporter_user),
            "HTTP_ORGANISATION_ID": organisation.id,
        }
        url = reverse(
            "applications:application_generated_document",
            kwargs={"pk": str(self.case.pk), "gcd_pk": str(self.generated_case_document.pk)},
        )

        response = self.client.get(url, **exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_generated_document_as_gov_user_failure(self):
        url = reverse(
            "applications:application_generated_document",
            kwargs={"pk": str(self.case.pk), "gcd_pk": str(self.generated_case_document.pk)},
        )

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
