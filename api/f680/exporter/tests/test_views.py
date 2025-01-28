from parameterized import parameterized
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from test_helpers.clients import DataTestClient

from api.f680.models import F680Application  # /PS-IGNORE
from api.f680.tests.factories import (
    F680ApplicationFactory,  # /PS-IGNORE
    SubmittedF680ApplicationFactory,  # /PS-IGNORE
)


class F680ApplicationViewSetTests(DataTestClient):  # /PS-IGNORE
    def setUp(self):
        super().setUp()
        self.maxDiff = 10000
        self.f680_url = reverse("exporter_f680:applications")

    def test_GET_list_empty_data_success(self):
        response = self.client.get(self.f680_url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"count": 0, "total_pages": 1, "results": []})

    def test_GET_list_success(self):
        f680_application = SubmittedF680ApplicationFactory(  # /PS-IGNORE
            organisation=self.organisation,
            submitted_by=self.exporter_user,
        )
        response = self.client.get(self.f680_url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "count": 1,
            "total_pages": 1,
            "results": [
                {
                    "id": str(f680_application.id),
                    "application": {"some": "json"},
                    "reference_code": f680_application.reference_code,
                    "organisation": {
                        "id": str(self.organisation.id),
                        "name": self.organisation.name,
                        "type": self.organisation.type,
                        "status": self.organisation.status,
                    },
                    "submitted_at": f680_application.submitted_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "submitted_by": {
                        "email": self.exporter_user.email,
                        "first_name": self.exporter_user.first_name,
                        "id": str(self.exporter_user.baseuser_ptr_id),
                        "last_name": self.exporter_user.last_name,
                        "pending": self.exporter_user.pending,
                    },
                }
            ],
        }
        self.assertEqual(response.data, expected_result)

    def test_GET_list_different_organisation_empty_results(self):
        _ = SubmittedF680ApplicationFactory()  # /PS-IGNORE
        response = self.client.get(self.f680_url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "count": 0,
            "total_pages": 1,
            "results": [],
        }
        self.assertEqual(response.data, expected_result)

    def test_GET_single_empty_data_not_found(self):
        url = reverse("exporter_f680:application", kwargs={"f680_application_id": uuid4()})
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_single_success(self):
        f680_application = SubmittedF680ApplicationFactory(  # /PS-IGNORE
            organisation=self.organisation,
            submitted_by=self.exporter_user,
        )
        url = reverse("exporter_f680:application", kwargs={"f680_application_id": f680_application.id})
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "id": str(f680_application.id),
            "application": {"some": "json"},
            "reference_code": f680_application.reference_code,
            "organisation": {
                "id": str(self.organisation.id),
                "name": self.organisation.name,
                "type": self.organisation.type,
                "status": self.organisation.status,
            },
            "submitted_at": f680_application.submitted_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "submitted_by": {
                "email": self.exporter_user.email,
                "first_name": self.exporter_user.first_name,
                "id": str(self.exporter_user.baseuser_ptr_id),
                "last_name": self.exporter_user.last_name,
                "pending": self.exporter_user.pending,
            },
        }
        self.assertEqual(response.data, expected_result)

    def test_GET_single_different_organisation_not_found(self):
        f680_application = SubmittedF680ApplicationFactory()  # /PS-IGNORE
        url = reverse("exporter_f680:application", kwargs={"f680_application_id": f680_application.id})
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_POST_create_success(self):
        data = {
            "application": {"name": "test application"},
        }
        response = self.client.post(self.f680_url, data, **self.exporter_headers)
        # create the application
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Grab the application from the DB
        application_id = response.data["id"]
        f680_application = F680Application.objects.get(id=application_id)  # /PS-IGNORE
        # Check the API result
        expected_result = {
            "id": str(f680_application.id),
            "application": {"name": "test application"},
            "reference_code": None,
            "organisation": {
                "id": str(self.organisation.id),
                "name": self.organisation.name,
                "type": self.organisation.type,
                "status": self.organisation.status,
            },
            "submitted_at": None,
            "submitted_by": None,
        }
        self.assertEqual(response.data, expected_result)

    def test_POST_create_bad_request(self):
        response = self.client.post(self.f680_url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = {
            "errors": {
                "application": [ErrorDetail("This field is required.", code="required")],
            },
        }
        self.assertEqual(response.data, expected_response)

    @parameterized.expand(
        [
            ({"id": uuid4()},),
            ({"status": "finalised"},),
            ({"reference_code": "myref"},),
            ({"organisation": uuid4()},),
            ({"submitted_at": timezone.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")},),
            ({"submitted_by": uuid4()},),
        ]
    )
    def test_POST_create_readonly_fields_ignored(self, extra_data):
        data = {
            "application": {"name": "test application"},
            **extra_data,
        }
        response = self.client.post(self.f680_url, data, **self.exporter_headers)
        # create the application
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Grab the application from the DB
        application_id = response.data["id"]
        f680_application = F680Application.objects.get(id=application_id)  # /PS-IGNORE
        # Check the API result
        expected_result = {
            "id": str(f680_application.id),
            "application": {"name": "test application"},
            "reference_code": None,
            "organisation": {
                "id": str(self.organisation.id),
                "name": self.organisation.name,
                "type": self.organisation.type,
                "status": self.organisation.status,
            },
            "submitted_at": None,
            "submitted_by": None,
        }
        self.assertEqual(response.data, expected_result)

    def test_PATCH_partial_update_empty_data_not_found(self):
        url = reverse("exporter_f680:application", kwargs={"f680_application_id": uuid4()})
        response = self.client.patch(url, {"application": {"new": "new value"}}, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_PATCH_partial_update_success(self):
        f680_application = SubmittedF680ApplicationFactory(  # /PS-IGNORE
            organisation=self.organisation,
            submitted_by=self.exporter_user,
            application={"old key": "old value"},
        )
        url = reverse("exporter_f680:application", kwargs={"f680_application_id": f680_application.id})
        patch_data = {"application": {"new key": "new value"}}
        response = self.client.patch(url, patch_data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "id": str(f680_application.id),
            "application": patch_data["application"],
            "reference_code": f680_application.reference_code,
            "organisation": {
                "id": str(self.organisation.id),
                "name": self.organisation.name,
                "type": self.organisation.type,
                "status": self.organisation.status,
            },
            "submitted_at": f680_application.submitted_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "submitted_by": {
                "email": self.exporter_user.email,
                "first_name": self.exporter_user.first_name,
                "id": str(self.exporter_user.baseuser_ptr_id),
                "last_name": self.exporter_user.last_name,
                "pending": self.exporter_user.pending,
            },
        }
        self.assertEqual(response.data, expected_result)

    def test_PATCH_partial_update_different_organisation_not_found(self):
        f680_application = SubmittedF680ApplicationFactory()  # /PS-IGNORE
        url = reverse("exporter_f680:application", kwargs={"f680_application_id": f680_application.id})
        response = self.client.patch(url, {"application": {"new": "new value"}}, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @parameterized.expand(
        [
            ({"id": uuid4()},),
            ({"status": "finalised"},),
            ({"reference_code": "myref"},),
            ({"organisation": uuid4()},),
            ({"submitted_at": timezone.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")},),
            ({"submitted_by": uuid4()},),
        ]
    )
    def test_PATCH_partial_update_readonly_fields_ignored(self, extra_data):
        # set up an existing application
        f680_application = F680ApplicationFactory(  # /PS-IGNORE
            organisation=self.organisation,
            submitted_at=None,
            reference_code=None,
            submitted_by=None,
        )
        # patch the application
        patch_data = {
            "application": {"name": "test application"},
            **extra_data,
        }
        url = reverse("exporter_f680:application", kwargs={"f680_application_id": f680_application.id})
        response = self.client.patch(url, patch_data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the API result
        expected_result = {
            "id": str(f680_application.id),
            "application": {"name": "test application"},
            "reference_code": f680_application.reference_code,
            "organisation": {
                "id": str(self.organisation.id),
                "name": self.organisation.name,
                "type": self.organisation.type,
                "status": self.organisation.status,
            },
            "submitted_at": None,
            "submitted_by": None,
        }
        self.assertEqual(response.data, expected_result)
