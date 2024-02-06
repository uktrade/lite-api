from unittest.mock import patch

from api.documents.tests.factories import DocumentFactory
from test_helpers.clients import DataTestClient


class DocumentTest(DataTestClient):
    @patch("api.documents.libraries.s3_operations.move_staged_document_to_processed")
    def test_move_staged_document(self, mocked_move_document):
        document = DocumentFactory()
        document.move_staged_document()
        mocked_move_document.assert_called_with(document.id, document.s3_key)
