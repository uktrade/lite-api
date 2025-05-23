import os
import tempfile

from django.test import override_settings, TestCase

from diff_pdf_visually import pdf_similar
from freezegun import freeze_time

from api.cases.generated_documents.signing import sign_pdf


CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_PATH = os.path.join(CURRENT_PATH, "data")
PDF_FILE_PATH = os.path.join(TEST_DATA_PATH, "dummy.pdf")
SIGNED_PDF_FILE_PATH = os.path.join(TEST_DATA_PATH, "signed.pdf")


class SignPDFTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(PDF_FILE_PATH, "rb") as pdf_file:
            cls.pdf_data = pdf_file.read()

    @override_settings(
        DOCUMENT_SIGNING_ENABLED=False,
    )
    def test_sign_pdf_skips_signing(self):
        output = sign_pdf(self.pdf_data, None, None, None)
        self.assertEqual(output, self.pdf_data)

    @override_settings(
        DOCUMENT_SIGNING_ENABLED=True,
        P12_CERTIFICATE="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",  # /PS-IGNORE
        CERTIFICATE_PASSWORD="testing",
        SIGNING_EMAIL="test@example.com",  # /PS-IGNORE
    )
    @freeze_time("2020-01-01 12:00:01")
    def test_sign_pdf_signing(self):

        document_signing_data = {
            "signing_reason": "test signing reason",
            "location": "test location",
            "image_name": "dit_emblem.png",
        }
        output = sign_pdf(
            self.pdf_data,
            document_signing_data["signing_reason"],
            document_signing_data["location"],
            document_signing_data["image_name"],
        )
        with tempfile.NamedTemporaryFile() as test_pdf_file:
            test_pdf_file.write(output)
            self.assertTrue(
                pdf_similar(
                    SIGNED_PDF_FILE_PATH,
                    test_pdf_file.name,
                ),
            )
