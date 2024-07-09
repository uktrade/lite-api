import pytest
import os

from django.conf import settings
from django.urls import reverse
from rest_framework import status

from api.applications.tests.factories import DenialEntityFactory
from api.external_data import models
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class ApplicationDenialMatchesOnApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application_case(self.organisation)
        self.application.status = get_case_status_by_status(CaseStatusEnum.INITIAL_CHECKS)
        self.application.save()
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        with open(file_path, "rb") as f:
            content = f.read()
            f.seek(0)
            self.total_denials = len(f.readlines()) - 1

        response = self.client.post(reverse("external_data:denial-list"), {"csv_file": content}, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.DenialEntity.objects.count(), self.total_denials)

    @pytest.mark.xfail(reason="This test is flaky and should be rewritten")
    # Occasionally causes this error:
    # django.db.utils.IntegrityError: duplicate key value violates unique constraint "external_data_denial_reference_05842cee_uniq"
    def test_adding_denials_to_application(self):
        data = [
            {"application": self.application.id, "denial": denial.id, "category": "exact" if (index % 2) else "partial"}
            for index, denial in enumerate(models.DenialEntity.objects.all()[:2])
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
        self.assertEqual(response.json()["count"], self.total_denials)

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
        self.assertEqual(response.json()["count"], self.total_denials)

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

    def test_revoke_denial_active_success(self):
        response = self.client.get(reverse("external_data:denial-list"), **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], self.total_denials)

        denials = response.json()["results"]

        # pick one and revoke it
        self.assertEqual(denials[0]["is_revoked"], False)
        denialentity = models.DenialEntity.objects.get(pk=denials[0]["id"])
        denialentity.denial.is_revoked = True
        denialentity.denial.save()

        response = self.client.patch(
            reverse("external_data:denial-detail", kwargs={"pk": denials[0]["id"]}),
            {
                "is_revoked": False,
            },
            **self.gov_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        self.assertEqual(response["is_revoked"], False)
        self.assertEqual(response["is_revoked_comment"], "")

    def test_view_denial_notifications_on_the_application(self):
        data = []
        for index in range(10):
            denial_entity = DenialEntityFactory()
            data.append(
                {
                    "application": self.application.id,
                    "denial_entity": denial_entity.id,
                    "category": "exact" if (index % 2) else "partial",
                }
            )

        url = reverse("applications:application_denial_matches", kwargs={"pk": self.application.id})
        response = self.client.post(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        denial_matches = response.json()["denial_matches"]
        self.assertEqual(len(denial_matches), 10)

        # remove one match
        response = self.client.delete(url, {"objects": [denial_matches[0]["id"]]}, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
