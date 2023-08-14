from _pytest.monkeypatch import MonkeyPatch
import uuid
from unittest import mock

from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient
from api.cases.generated_documents.tests.factories import GeneratedCaseDocumentFactory
from api.cases.generated_documents import views
from api.letter_templates.models import LetterTemplate


class GeneratedDocumentSendTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)

    def test_post_generated_document_missing(self):

        url = reverse(
            "cases:generated_documents:send_generated_document",
            kwargs={"document_pk": uuid.uuid4(), "pk": self.case.id},
        )
        response = self.client.post(url, **self.gov_headers)
        assert response.status_code == 404

    def test_post_no_notification(self):
        generated_document = GeneratedCaseDocumentFactory(
            template=LetterTemplate.objects.first(),
            case=self.case,
            visible_to_exporter=False,
        )

        url = reverse(
            "cases:generated_documents:send_generated_document",
            kwargs={"document_pk": generated_document.id, "pk": self.case.id},
        )
        response = self.client.post(url, **self.gov_headers)
        assert response.status_code == 200
        assert response.json() == {"notification_sent": False}
        generated_document.refresh_from_db()
        assert generated_document.visible_to_exporter == True

    def test_post_with_notification(self):
        mocked_notify_function = mock.Mock()
        MonkeyPatch().setitem(views.NOTIFICATION_FUNCTIONS, "inform_letter", mocked_notify_function)

        generated_document = GeneratedCaseDocumentFactory(
            template=LetterTemplate.objects.first(),
            case=self.case,
            visible_to_exporter=False,
        )
        generated_document.template.layout.filename = "inform_letter"
        generated_document.template.layout.save()

        url = reverse(
            "cases:generated_documents:send_generated_document",
            kwargs={"document_pk": generated_document.id, "pk": self.case.id},
        )
        response = self.client.post(url, **self.gov_headers)
        assert response.status_code == 200
        assert response.json() == {"notification_sent": True}
        generated_document.refresh_from_db()
        assert generated_document.visible_to_exporter == True
        mocked_notify_function.assert_called_with(self.case.get_case())
