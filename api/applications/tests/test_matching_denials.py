import csv
import io
import pytest

from django.urls import reverse
from faker import Faker
from rest_framework import status

from api.external_data import models, serializers
from test_helpers.clients import DataTestClient


class ApplicationDenialMatchesOnApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.faker = Faker()
        self.application = self.create_standard_application_case(self.organisation)
        denials = [
            {name: self.faker.word() for name in serializers.DenialFromCSVFileSerializer.required_headers}
            for _ in range(5)
        ]

        content = io.StringIO()
        writer = csv.DictWriter(
            content,
            fieldnames=[*serializers.DenialFromCSVFileSerializer.required_headers, "field_n"],
            delimiter=",",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(denials)
        response = self.client.post(
            reverse("external_data:denial-list"), {"csv_file": content.getvalue()}, **self.gov_headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.Denial.objects.count(), 5)

    @pytest.mark.xfail(reason="This test is flaky and should be rewritten")
    # Occasionally causes this error:
    # django.db.utils.IntegrityError: duplicate key value violates unique constraint "external_data_denial_reference_05842cee_uniq"
    def test_adding_denials_to_application(self):
        data = [
            {"application": self.application.id, "denial": denial.id, "category": "exact" if (index % 2) else "partial"}
            for index, denial in enumerate(models.Denial.objects.all()[:2])
        ]
        url = reverse("applications:application_denial_matches", kwargs={"pk": self.application.id})
        response = self.client.post(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        denial_matches = response.json()["denial_matches"]
        self.assertEqual(len(denial_matches), 2)

        # remove one match
        response = self.client.delete(url, {"objects": [denial_matches[0]["id"]]}, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_revoke_denial_without_comment_failure(self):
        response = self.client.get(reverse("external_data:denial-list"), **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 5)

        denials = response.json()["results"]

        # pick one and revoke it without comment
        self.assertEqual(denials[0]["is_revoked"], False)
        response = self.client.patch(
            reverse("external_data:denial-detail", kwargs={"pk": denials[0]["id"]}),
            {"is_revoked": True},
            **self.gov_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("is_revoked_comment" in response.json()["errors"], True)

    def test_revoke_denial_success(self):
        response = self.client.get(reverse("external_data:denial-list"), **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 5)

        denials = response.json()["results"]

        # pick one and revoke it
        self.assertEqual(denials[0]["is_revoked"], False)
        response = self.client.patch(
            reverse("external_data:denial-detail", kwargs={"pk": denials[0]["id"]}),
            {"is_revoked": True, "is_revoked_comment": "This denial is no longer active"},
            **self.gov_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        self.assertEqual(response["is_revoked"], True)
        self.assertEqual(response["is_revoked_comment"], "This denial is no longer active")
