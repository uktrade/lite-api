from rest_framework import status
from rest_framework.reverse import reverse

from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class LetterLayoutsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.letter_layout = LetterLayout.objects.first()

    def test_get_letter_layouts_success(self):
        url = reverse("static:letter_layouts:letter_layouts")
        response = self.client.get(url)
        response_data = response.json()["results"][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.letter_layout.id))
        self.assertEqual(response_data["filename"], self.letter_layout.filename)
        self.assertEqual(response_data["name"], self.letter_layout.name)

    def test_get_letter_layout_success(self):
        url = reverse(
            "static:letter_layouts:letter_layout", kwargs={"pk": self.letter_layout.id}
        )
        response = self.client.get(url)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.letter_layout.id))
        self.assertEqual(response_data["filename"], self.letter_layout.filename)
        self.assertEqual(response_data["name"], self.letter_layout.name)
