import json

from rest_framework import status

from django.urls import reverse

from test_helpers.clients import DataTestClient

from api.staticdata.statuses.factories import CaseStatusFactory


class StatusPropertiesTests(DataTestClient):
    def test_get_status(self):
        case_status = CaseStatusFactory(
            status="madeup",
        )

        url = reverse(
            "staticdata:statuses:case_status_properties",
            kwargs={
                "status": case_status.status,
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content),
            {
                "is_read_only": case_status.is_read_only,
                "is_terminal": case_status.is_terminal,
                "is_major_editable": case_status.is_major_editable,
            },
        )
