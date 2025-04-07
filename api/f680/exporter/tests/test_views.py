import pytest
from parameterized import parameterized
from uuid import uuid4

from freezegun import freeze_time

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

pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


# TODO: Move the below DataTestClient tests over to pytest style (class below)
class F680ApplicationViewSetTests(DataTestClient):  # /PS-IGNORE
    def setUp(self):
        super().setUp()
        self.maxDiff = 10000
        self.f680_url = reverse("exporter_f680:applications")

    def test_GET_list_empty_data_success(self):
        response = self.client.get(self.f680_url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"count": 0, "total_pages": 1, "results": []})

    def test_GET_list_submitted_only_no_results_success(self):
        f680_application = SubmittedF680ApplicationFactory(organisation=self.organisation)
        response = self.client.get(self.f680_url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"count": 0, "total_pages": 1, "results": []})

    def test_GET_list_success(self):
        f680_application = F680ApplicationFactory(organisation=self.organisation)
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
                    "submitted_at": None,
                    "submitted_by": None,
                }
            ],
        }
        self.assertEqual(response.data, expected_result)

    def test_GET_list_different_organisation_empty_results(self):
        _ = F680ApplicationFactory()
        response = self.client.get(self.f680_url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "count": 0,
            "total_pages": 1,
            "results": [],
        }
        self.assertEqual(response.data, expected_result)

    def test_GET_single_empty_data_not_found(self):
        f680_application = SubmittedF680ApplicationFactory(organisation=self.organisation)
        url = reverse("exporter_f680:application", kwargs={"f680_application_id": f680_application.id})
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_single_submitted_application_not_found(self):
        url = reverse("exporter_f680:application", kwargs={"f680_application_id": uuid4()})
        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_single_success(self):
        f680_application = F680ApplicationFactory(organisation=self.organisation)
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
            "submitted_at": None,
            "submitted_by": None,
        }
        self.assertEqual(response.data, expected_result)

    def test_GET_single_different_organisation_not_found(self):
        f680_application = F680ApplicationFactory()
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

    def test_PATCH_partial_update_submitted_application_not_found(self):
        f680_application = SubmittedF680ApplicationFactory(organisation=self.organisation)
        url = reverse("exporter_f680:application", kwargs={"f680_application_id": f680_application.id})
        response = self.client.patch(url, {"application": {"new": "new value"}}, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_PATCH_partial_update_success(self):
        f680_application = F680ApplicationFactory(
            organisation=self.organisation,
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
            "submitted_at": None,
            "submitted_by": None,
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


class TestF680ApplicationViewSet:

    @freeze_time("2025-01-01 12:00:01")
    def test_POST_submit_success(
        self, api_client, exporter_headers, exporter_user, organisation, data_application_json
    ):
        f680_application = F680ApplicationFactory(
            organisation=organisation,
            application=data_application_json,
            reference_code=None,
        )
        request_data = {"agreed_to_foi": True, "foi_reason": "Some reason"}
        url = reverse("exporter_f680:application_submit", kwargs={"f680_application_id": f680_application.id})
        response = api_client.post(url, request_data, **exporter_headers)
        assert response.status_code == status.HTTP_200_OK
        f680_application.refresh_from_db()

        assert f680_application.status.status == "submitted"
        assert f680_application.submitted_at == timezone.now()
        assert f680_application.sla_days == 0
        assert f680_application.submitted_by == exporter_user
        assert f680_application.reference_code.startswith("F680")
        assert f680_application.agreed_to_foi == True
        assert f680_application.foi_reason == "Some reason"

        expected_result = {
            "id": str(f680_application.id),
            "application": data_application_json,
            "reference_code": f680_application.reference_code,
            "organisation": {
                "id": str(organisation.id),
                "name": organisation.name,
                "type": organisation.type,
                "status": organisation.status,
            },
            "submitted_at": timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "submitted_by": {
                "email": exporter_user.email,
                "first_name": exporter_user.first_name,
                "id": str(exporter_user.baseuser_ptr_id),
                "last_name": exporter_user.last_name,
                "pending": exporter_user.pending,
            },
        }
        assert response.data == expected_result

    @pytest.mark.parametrize(
        "application_json, expected_result",
        (
            (
                {},
                {
                    "errors": {
                        "sections": [ErrorDetail(string="This field is required.", code="required")],
                    }
                },
            ),
            (
                {
                    "sections": {
                        "approval_type": {},
                        "product_information": {},
                        "user_information": {},
                        "general_application_details": {},
                    },
                },
                {
                    "errors": {
                        "sections": {
                            "product_information": {
                                "type": [ErrorDetail(string="This field is required.", code="required")],
                                "fields": [ErrorDetail(string="This field is required.", code="required")],
                            },
                            "user_information": {
                                "type": [ErrorDetail(string="This field is required.", code="required")],
                                "items": [ErrorDetail(string="This field is required.", code="required")],
                            },
                            "general_application_details": {
                                "type": [ErrorDetail(string="This field is required.", code="required")],
                                "fields": [ErrorDetail(string="This field is required.", code="required")],
                            },
                            "approval_type": {
                                "type": [ErrorDetail(string="This field is required.", code="required")],
                                "fields": [ErrorDetail(string="This field is required.", code="required")],
                            },
                        },
                    }
                },
            ),
            (
                {
                    "sections": {
                        "approval_type": {"type": "multiple", "fields": {}},
                        "product_information": {"type": "single", "fields": {}},
                        "user_information": {"type": "multiple", "items": []},
                        "general_application_details": {"type": "single", "fields": {}},
                    },
                },
                {
                    "errors": {
                        "sections": {
                            "product_information": {
                                "fields": {
                                    "product_name": [ErrorDetail(string="This field is required.", code="required")],
                                    "product_description": [
                                        ErrorDetail(string="This field is required.", code="required")
                                    ],
                                }
                            },
                            "user_information": {
                                "items": {
                                    "non_field_errors": [
                                        ErrorDetail(
                                            string="Ensure this field has at least 1 elements.", code="min_length"
                                        )
                                    ]
                                }
                            },
                            "general_application_details": {
                                "fields": {"name": [ErrorDetail(string="This field is required.", code="required")]}
                            },
                            "approval_type": {
                                "type": [
                                    ErrorDetail(string='"multiple" is not a valid choice.', code="invalid_choice")
                                ],
                                "fields": {
                                    "approval_choices": [ErrorDetail(string="This field is required.", code="required")]
                                },
                            },
                        },
                    }
                },
            ),
        ),
    )
    def test_POST_submit_application_json_format_incorrect_responds_400(
        self, application_json, expected_result, api_client, exporter_headers, exporter_user, organisation
    ):
        f680_application = F680ApplicationFactory(
            organisation=organisation,
            application=application_json,
            reference_code=None,
        )
        url = reverse("exporter_f680:application_submit", kwargs={"f680_application_id": f680_application.id})
        response = api_client.post(url, **exporter_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == expected_result

    def test_POST_submit_different_organisation_not_found(self, api_client, exporter_headers):
        f680_application = SubmittedF680ApplicationFactory()
        url = reverse("exporter_f680:application_submit", kwargs={"f680_application_id": f680_application.id})
        response = api_client.post(url, {"application": {"new": "new value"}}, **exporter_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_POST_submit_empty_data_not_found(self, api_client, exporter_headers):
        url = reverse("exporter_f680:application_submit", kwargs={"f680_application_id": uuid4()})
        response = api_client.post(url, **exporter_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_POST_submit_submitted_application_not_found(self, api_client, exporter_headers, organisation):
        f680_application = SubmittedF680ApplicationFactory(organisation=organisation)
        url = reverse("exporter_f680:application_submit", kwargs={"f680_application_id": f680_application.id})
        response = api_client.post(url, **exporter_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
