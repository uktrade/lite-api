from django.urls import reverse
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APITestCase, override_settings
from test_helpers.helpers import reload_urlconf


@override_settings(MOCK_VIRUS_SCAN_ACTIVATE_ENDPOINTS=True)
class TestMockVirusScan(APITestCase):
    def setUp(self):
        super().setUp()

        reload_urlconf()
        self.url = reverse("mock_virus_scan:scan")
        self.client = Client()

    def test_mock_scan_virus_file(self):

        # eicar standard industry pattern used to test positive virus
        eicar_content = b"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

        response = self.client.post(
            self.url,
            {
                "file": [
                    SimpleUploadedFile("file 1", eicar_content),
                ]
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"malware": True})

    def test_mock_scan_no_virus_file(self):

        response = self.client.post(
            self.url,
            {
                "file": [
                    SimpleUploadedFile("file 1", b"no virus"),
                ]
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"malware": False})

    def test_mock_scan_no_file(self):

        response = self.client.post(
            self.url,
            data={},
        )

        self.assertEqual(response.status_code, 400)
