from django.urls import reverse

from cases.models import Case
from test_helpers.clients import DataTestClient


class CaseEndUserDocumentTests(DataTestClient):
    def setUp(self):
        super().setUp()

    def test_case_contains_end_user_document(self):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user has a document attached
        And the end user document has been scanned by an AV
        And the AV marked the document as safe
        And the application is submitted
        When the case is retrieved
        Then the case it contains the end user document
        And the data in the document is the same as the data in original draft's end user document
        """
        # assemble
        draft = self.create_standard_application(organisation=self.organisation)
        case = self.submit_application(draft)

        # act
        response = self.client.get(reverse("cases:case", kwargs={"pk": case.id}), **self.gov_headers)

        # assert
        data = response.json()

        self.assertIsNotNone(data["case"]["application"]["destinations"]["data"]["document"])
        self.assertEquals(
            "document_name.pdf", data["case"]["application"]["destinations"]["data"]["document"]["name"],
        )
        self.assertEquals(
            True, data["case"]["application"]["destinations"]["data"]["document"]["safe"],
        )
