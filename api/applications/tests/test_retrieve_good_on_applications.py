from django.urls import reverse
from rest_framework import status

from api.goods.enums import GoodStatus
from test_helpers.clients import DataTestClient


class RetrieveGoodsTests(DataTestClient):
    def test_exporter_retrieve_a_good_on_application(self):
        self.create_draft_standard_application(self.organisation)
        self.good_on_application.good.status = GoodStatus.VERIFIED
        self.good_on_application.good.save()

        url = reverse(
            "applications:good_on_application",
            kwargs={"obj_pk": self.good_on_application.id},
        )

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("audit_trail", response.json())

    def test_caseworker_retrieve_a_good_on_application(self):
        self.create_draft_standard_application(self.organisation)
        self.good_on_application.good.status = GoodStatus.VERIFIED
        self.good_on_application.good.save()

        url = reverse(
            "applications:good_on_application_internal",
            kwargs={"obj_pk": self.good_on_application.id},
        )

        response = self.client.get(url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("audit_trail", response.json())
