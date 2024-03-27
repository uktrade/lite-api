from django.conf import settings
from django.test import override_settings

from api.core.helpers import get_exporter_frontend_url
import pytest
import datetime
from unittest import mock
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from api.cases.celery_tasks import (
    schedule_all_ecju_query_chaser_emails,
    send_ecju_query_chaser_email,
    mark_ecju_query_as_sent,
)
from api.cases.tests.factories import EcjuQueryFactory
from api.users.models import BaseNotification
from faker import Faker
from gov_notify.payloads import ExporterECJUQueryChaser
from parameterized import parameterized
from rest_framework import status
from freezegun import freeze_time

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer
from api.cases.enums import ECJUQueryType
from api.cases.models import EcjuQuery
from api.picklists.enums import PicklistType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from gov_notify.enums import TemplateType
from api.cases.models import CaseNoteMentions

faker = Faker()


class ECJUQueriesViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.case2 = self.create_standard_application_case(self.organisation)
        self.no_ecju_queries_case = self.create_standard_application_case(self.organisation)

        self.url = reverse("cases:case_ecju_queries", kwargs={"pk": self.case.id})

        self.ecju_query_1 = EcjuQueryFactory(
            question="ECJU Query 1", case=self.case, raised_by_user=self.gov_user, response=None
        )

        self.team_2 = self.create_team("TAU")
        self.gov_user2_email = "bob@slob.com"
        self.gov_user_2 = self.create_gov_user(self.gov_user2_email, self.team_2)

        self.ecju_query_2 = EcjuQueryFactory(
            question="ECJU Query 2",
            case=self.case,
            response="I have a response",
            raised_by_user=self.gov_user_2,
            responded_by_user=self.base_user,
            query_type=PicklistType.ECJU,
        )

        self.ecju_query_3 = EcjuQueryFactory(question="ECJU Query 3", case=self.case2, raised_by_user=self.gov_user)

    def test_view_case_with_ecju_queries_as_gov_user_successful(self):
        """
        Given a case with ECJU queries on it
        When a gov user requests the ECJU queries for the case
        Then the request is successful
        """
        # Act
        response = self.client.get(self.url, **self.gov_headers)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_case_with_ecju_queries_as_exporter_user_successful(self):
        """
        Given a case with ECJU queries on it
        When an exporter user requests the ECJU queries for the case
        Then the request is successful
        """
        # Act
        response = self.client.get(self.url, **self.exporter_headers)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_correct_ecju_query_details_are_returned_to_gov_user(self):
        """
        Given a case with ECJU queries
        When a gov user requests the ECJU queries for the case
        Then the expected ECJU queries and properties are returned
        """
        # Act
        response = self.client.get(self.url, **self.gov_headers)

        # Assert
        response_json = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_json.get("ecju_queries")), 2)

        returned_ecju_query_1 = response_json.get("ecju_queries")[0]
        self.assertEqual(returned_ecju_query_1.get("question"), "ECJU Query 1")
        self.assertEqual(returned_ecju_query_1.get("response"), None)

        returned_ecju_query_2 = response_json.get("ecju_queries")[1]
        self.assertEqual(returned_ecju_query_2.get("question"), "ECJU Query 2")
        self.assertEqual(returned_ecju_query_2.get("response"), "I have a response")

    def test_correct_ecju_query_details_are_returned_to_exporter_user(self):
        """
        Given a case with ECJU queries
        When an exporter user requests the ECJU queries for the case
        Then the expected ECJU queries and properties are returned
        """
        # Act
        response = self.client.get(self.url, **self.exporter_headers)

        # Assert
        response_json = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_json.get("ecju_queries")), 2)

        returned_ecju_query_1 = response_json.get("ecju_queries")[0]
        self.assertEqual(returned_ecju_query_1.get("question"), "ECJU Query 1")
        self.assertEqual(returned_ecju_query_1.get("response"), None)
        self.assertEqual(returned_ecju_query_1.get("team")["name"], self.ecju_query_1.team.name)
        self.assertEqual(returned_ecju_query_1.get("is_query_closed"), self.ecju_query_1.is_query_closed)
        # We can't predict exactly when the query is created so we settle for the fact that its set
        self.assertIsNotNone(returned_ecju_query_1.get("created_at"))

        returned_ecju_query_2 = response_json.get("ecju_queries")[1]
        self.assertEqual(returned_ecju_query_2.get("question"), "ECJU Query 2")
        self.assertEqual(returned_ecju_query_2.get("response"), "I have a response")
        self.assertEqual(returned_ecju_query_2.get("team")["name"], self.ecju_query_2.team.name)
        self.assertEqual(returned_ecju_query_2.get("is_query_closed"), self.ecju_query_2.is_query_closed)
        # We can't predict exactly when the query is created so we settle for the fact that its set
        self.assertIsNotNone(returned_ecju_query_1.get("created_at"))

    def test_view_case_without_ecju_queries(self):
        """
        Given a case with no ECJU queries
        When a gov user requests the ECJU queries for the case
        Then the request is successful and an empty list is returned
        """
        # Assemble
        no_queries_url = reverse("cases:case_ecju_queries", kwargs={"pk": self.no_ecju_queries_case.id})

        # Act
        response = self.client.get(no_queries_url, **self.gov_headers)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get("ecju_queries")), 0)

    def test_gov_user_can_get_an_individual_ecju_query(self):
        """
        Given an ECJU query
        When a gov user requests the ECJU query by ID
        Then the request is successful and the details of the ECJU query are returned
        """
        case = self.create_standard_application_case(self.organisation)
        ecju_query = EcjuQueryFactory(question="Ble", case=case, response=None)

        url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})

        # Act
        response = self.client.get(url, **self.gov_headers)

        # Assert
        response_data = response.json()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(str(ecju_query.id), response_data["ecju_query"]["id"])
        self.assertEqual(str(ecju_query.question), response_data["ecju_query"]["question"])
        self.assertEqual(ecju_query.response, None)
        self.assertEqual(str(ecju_query.case.id), response_data["ecju_query"]["case"])
        self.assertEqual(ecju_query.is_query_closed, response_data["ecju_query"]["is_query_closed"])
        self.assertEqual(ecju_query.is_manually_closed, response_data["ecju_query"]["is_manually_closed"])

    def test_ecju_query_open_query_count(self):
        """
        Given an ECJU query
        When a user request no of open queries on a case
        Then the request is successful  we return the number of open ECJUQueries
        """
        case = self.create_standard_application_case(self.organisation)
        EcjuQueryFactory(question="open query 1", case=case, raised_by_user=self.gov_user, response=None)

        url = reverse("cases:case_ecju_query_open_count", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, response_data["count"])

        EcjuQueryFactory(
            question="open query 2",
            case=case,
            responded_by_user=self.exporter_user.baseuser_ptr,
            response="I have a response only",
        )

        response = self.client.get(url, **self.gov_headers)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, response_data["count"])

    def test_ecju_query_open_query_count_responded_return_zero(self):
        """
        Given an ECJU query
        When a user request no of open queries on a case
         Then the request is successful  we return 0 as open queries
        """
        case = self.create_standard_application_case(self.organisation)

        EcjuQueryFactory(
            question="closed query",
            case=case,
            responded_by_user=self.exporter_user.baseuser_ptr,
            responded_at=timezone.now(),
        )

        url = reverse("cases:case_ecju_query_open_count", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(0, response_data["count"])

    @parameterized.expand(
        [
            (
                {
                    "year": 2022,
                    "month": 11,
                    "day": 30,
                    "hour": 9,
                    "minute": 50,
                    "tzinfo": timezone.utc,
                },
                291,
            ),
            (
                {
                    "year": 2023,
                    "month": 12,
                    "day": 15,
                    "hour": 13,
                    "minute": 37,
                    "tzinfo": timezone.utc,
                },
                28,
            ),
            (
                {
                    "year": 2024,
                    "month": 1,
                    "day": 1,
                    "hour": 12,
                    "minute": 30,
                    "tzinfo": timezone.utc,
                },
                19,
            ),
            ({"year": 2024, "month": 1, "day": 22, "hour": 15, "minute": 40, "tzinfo": timezone.utc}, 5),
        ]
    )
    @freeze_time("2024-01-29 15:00:00")
    def test_ecju_query_shows_correct_open_working_days_for_open_query(
        self, created_at_datetime_kwargs, expected_working_days
    ):
        case = self.create_standard_application_case(self.organisation)
        created_at_datetime = timezone.datetime(**created_at_datetime_kwargs)
        ecju_query = EcjuQueryFactory(
            question="this is the question",
            response=None,
            responded_at=None,
            case=case,
            created_at=created_at_datetime,
        )

        url = reverse("cases:case_ecju_queries", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        assert response_data["ecju_queries"][0]["open_working_days"] == expected_working_days

    @parameterized.expand(
        [
            (
                {
                    "year": 2022,
                    "month": 11,
                    "day": 30,
                    "hour": 9,
                    "minute": 50,
                    "tzinfo": timezone.utc,
                },
                365,
                252,
            ),
            (
                {
                    "year": 2023,
                    "month": 12,
                    "day": 15,
                    "hour": 13,
                    "minute": 37,
                    "tzinfo": timezone.utc,
                },
                30,
                18,
            ),
            ({"year": 2024, "month": 1, "day": 22, "hour": 15, "minute": 40, "tzinfo": timezone.utc}, 7, 5),
            (
                {
                    "year": 2024,
                    "month": 1,
                    "day": 28,
                    "hour": 12,
                    "minute": 6,
                    "tzinfo": timezone.utc,
                },
                1,
                0,
            ),
        ],
    )
    def test_ecju_query_shows_correct_open_working_days_for_closed_query(
        self, created_at_datetime_kwargs, calendar_days, expected_working_days
    ):
        case = self.create_standard_application_case(self.organisation)
        created_at_datetime = timezone.datetime(**created_at_datetime_kwargs)
        responded_at_datetime = created_at_datetime + timedelta(days=calendar_days)
        ecju_query = EcjuQueryFactory(
            question="this is the question",
            response="some response text",
            responded_at=responded_at_datetime,
            case=case,
            created_at=created_at_datetime,
        )

        url = reverse("cases:case_ecju_queries", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        assert response_data["ecju_queries"][0]["open_working_days"] == expected_working_days


class ECJUQueriesCreateTest(DataTestClient):
    @parameterized.expand([ECJUQueryType.ECJU, ECJUQueryType.PRE_VISIT_QUESTIONNAIRE, ECJUQueryType.COMPLIANCE_ACTIONS])
    @mock.patch("api.cases.views.views.notify.notify_exporter_ecju_query")
    def test_gov_user_can_create_ecju_queries(self, query_type, mock_notify):
        """
        When a GOV user submits a valid query to a case
        Then the request is successful and the query is saved
        And an email is sent to the user
        """
        case = self.create_standard_application_case(self.organisation)
        url = reverse("cases:case_ecju_queries", kwargs={"pk": case.id})
        data = {"question": "Test ECJU Query question?", "query_type": query_type}

        response = self.client.post(url, data, **self.gov_headers)
        response_data = response.json()
        ecju_query = EcjuQuery.objects.get(case=case)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response_data["ecju_query_id"], str(ecju_query.id))
        self.assertEqual("Test ECJU Query question?", ecju_query.question)
        self.assertEqual(False, ecju_query.is_query_closed)
        self.assertEqual(False, ecju_query.is_manually_closed)

        mock_notify.assert_called_with(case.id)

    @parameterized.expand([[""], [None], ["a" * 5001]])
    def test_submit_invalid_data_failure(self, data):
        """
        When a GOV user submits a query with invalid data to a case
        Then the request fails due to the invalid data
        And no query is created
        """
        case = self.create_standard_application_case(self.organisation)
        url = reverse("cases:case_ecju_queries", kwargs={"pk": case.id})

        response = self.client.post(url, {"question": data}, **self.gov_headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertFalse(EcjuQuery.objects.exists())


class ECJUQueriesResponseTests(DataTestClient):
    @mock.patch("api.documents.libraries.s3_operations.get_object")
    @mock.patch("api.documents.libraries.av_operations.scan_file_for_viruses")
    def add_query_document(self, case_id, query_id, expected_status, mock_virus_scan, mock_s3_operations_get_object):
        mock_virus_scan.return_value = False
        url = reverse("cases:case_ecju_query_add_document", kwargs={"pk": case_id, "query_pk": query_id})
        file_name = faker.file_name()
        data = {
            "name": file_name,
            "s3_key": f"{file_name}_{faker.uuid4()}",
            "description": faker.text(),
            "size": 1 << 10,
            "virus_scanned_at": timezone.now(),
        }
        mock_s3_operations_get_object.return_value = data
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, expected_status)
        return response.json()

    def _test_exporter_responds_to_query(self, add_documents, query_type):
        case = self.create_standard_application_case(self.organisation)
        url = reverse("cases:case_ecju_queries", kwargs={"pk": case.id})
        data = {"question": "Please provide required documents", "query_type": query_type}

        response = self.client.post(url, data, **self.gov_headers)
        response_data = response.json()
        ecju_query = EcjuQuery.objects.get(case=case)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response_data["ecju_query_id"], str(ecju_query.id))
        self.assertEqual("Please provide required documents", ecju_query.question)
        self.assertIsNone(ecju_query.response)

        documents_to_be_added = []
        if add_documents:
            documents_to_be_added = [
                self.add_query_document(case.id, ecju_query.id, status.HTTP_201_CREATED) for _ in range(5)
            ]

        query_response_url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})
        data = {"response": "Attached the requested documents"}
        response = self.client.put(query_response_url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()["ecju_query"]
        self.assertEqual(response["response"], data["response"])

        response_get = self.client.get(query_response_url, data, **self.gov_headers)
        self.assertEqual(False, response_get.json()["ecju_query"]["is_manually_closed"])

        query_response_audit = Audit.objects.filter(verb=AuditType.ECJU_QUERY_RESPONSE)
        self.assertTrue(query_response_audit.exists())
        audit_obj = query_response_audit.first()
        audit_text = AuditSerializer(audit_obj).data["text"]
        audit_additional_text = AuditSerializer(audit_obj).data["additional_text"]
        self.assertEqual(audit_text, " responded to an ECJU Query.")
        self.assertEqual(audit_additional_text, "Attached the requested documents")
        self.assertEqual(audit_obj.target.id, case.id)

        if add_documents:
            self.assertEqual(len(response["documents"]), len(documents_to_be_added))

    @parameterized.expand([ECJUQueryType.ECJU, ECJUQueryType.PRE_VISIT_QUESTIONNAIRE, ECJUQueryType.COMPLIANCE_ACTIONS])
    def test_exporter_responds_to_query(self, query_type):
        """Respond to queries without and with adding documents"""
        self._test_exporter_responds_to_query(False, query_type)
        self._test_exporter_responds_to_query(True, query_type)

    def test_caseworker_manually_closes_query(self):
        case = self.create_standard_application_case(self.organisation)
        ecju_query = self.create_ecju_query(case, question="provide details please", gov_user=self.gov_user)

        query_response_url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})
        data = {"response": "exporter provided details"}

        self.assertEqual(1, BaseNotification.objects.filter(object_id=ecju_query.id).count())

        response = self.client.put(query_response_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()["ecju_query"]
        self.assertEqual(response["response"], data["response"])

        query_response_audit = Audit.objects.filter(verb=AuditType.ECJU_QUERY_MANUALLY_CLOSED)
        self.assertTrue(query_response_audit.exists())
        audit_obj = query_response_audit.first()
        audit_text = AuditSerializer(audit_obj).data["text"]
        audit_additional_text = AuditSerializer(audit_obj).data["additional_text"]

        self.assertEqual(audit_text, " manually closed a query.")
        self.assertEqual(audit_additional_text, "exporter provided details")
        self.assertEqual(audit_obj.target.id, case.id)
        self.assertEqual(0, BaseNotification.objects.filter(object_id=ecju_query.id).count())

    def test_close_query_has_optional_response_exporter(self):
        case = self.create_standard_application_case(self.organisation)
        ecju_query = self.create_ecju_query(case, question="provide details please", gov_user=self.gov_user)

        self.assertIsNone(ecju_query.responded_at)

        query_response_url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})

        data = {"response": ""}
        response = self.client.put(query_response_url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_ecju_query = response.json()["ecju_query"]
        self.assertIsNone(response_ecju_query["response"])
        self.assertIsNotNone(response_ecju_query["responded_at"])

    @parameterized.expand(["", None])
    def test_close_query_has_required_response_govuser(self, response_value):
        case = self.create_standard_application_case(self.organisation)
        ecju_query = self.create_ecju_query(case, question="provide details please", gov_user=self.gov_user)

        self.assertIsNone(ecju_query.responded_at)
        self.assertEqual(1, BaseNotification.objects.filter(object_id=ecju_query.id).count())

        query_response_url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})

        data = {"response": response_value}

        response = self.client.put(query_response_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], "Enter a reason why you are closing the query")

    def test_caseworker_manually_closes_query_exporter_responds_raises_error(self):
        case = self.create_standard_application_case(self.organisation)
        ecju_query = self.create_ecju_query(case, question="provide details please", gov_user=self.gov_user)

        query_response_url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})
        data = {"response": "exporter provided details"}

        response = self.client.put(query_response_url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()["ecju_query"]
        self.assertEqual(response["response"], data["response"])

        response = self.client.put(
            query_response_url, {"response": "attempting to response to closed query"}, **self.exporter_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_caseworker_manually_closes_query_already_closed_raises_error(self):
        case = self.create_standard_application_case(self.organisation)
        ecju_query = self.create_ecju_query(case, question="provide details please", gov_user=self.gov_user)

        query_response_url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})
        data = {"response": "exporter provided details"}

        response = self.client.put(query_response_url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()["ecju_query"]
        self.assertEqual(response["response"], data["response"])

        response = self.client.put(
            query_response_url, {"response": "attempting to close and closed query"}, **self.gov_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_exporter_cannot_respond_to_same_ecju_query_twice(self):
        """Once a query is responded it is closed so ensure we cannot respond to closed queries"""
        case = self.create_standard_application_case(self.organisation)
        url = reverse("cases:case_ecju_queries", kwargs={"pk": case.id})
        data = {"question": "Please provide more details", "query_type": ECJUQueryType.ECJU}

        response = self.client.post(url, data, **self.gov_headers)
        response_data = response.json()
        ecju_query = EcjuQuery.objects.get(case=case)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response_data["ecju_query_id"], str(ecju_query.id))
        self.assertEqual("Please provide more details", ecju_query.question)
        self.assertIsNone(ecju_query.response)

        url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})
        data = {"response": "Additional details included"}
        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()["ecju_query"]
        self.assertEqual(response["response"], data["response"])

        new_data = {"response": "Overwriting previous response"}
        response = self.client.put(url, new_data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()["ecju_query"]
        self.assertEqual(response["response"], data["response"])

    def test_exporter_cannot_add_documents_to_closed_query(self):
        """Once a query is responded it is closed so ensure we cannot add documents to closed queries"""
        case = self.create_standard_application_case(self.organisation)
        url = reverse("cases:case_ecju_queries", kwargs={"pk": case.id})
        data = {"question": "Please provide required documents", "query_type": ECJUQueryType.ECJU}

        response = self.client.post(url, data, **self.gov_headers)
        response_data = response.json()
        ecju_query = EcjuQuery.objects.get(case=case)

        self.assertEqual(1, BaseNotification.objects.filter(object_id=ecju_query.id).count())
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response_data["ecju_query_id"], str(ecju_query.id))
        self.assertEqual("Please provide required documents", ecju_query.question)
        self.assertIsNone(ecju_query.response)

        self.add_query_document(case.id, ecju_query.id, status.HTTP_201_CREATED)

        self.assertEqual(1, BaseNotification.objects.filter(object_id=ecju_query.id).count())

        query_response_url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})
        data = {"response": "Attached the requested documents"}
        response = self.client.put(query_response_url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()["ecju_query"]
        self.assertEqual(response["response"], data["response"])
        self.assertEqual(len(response["documents"]), 1)
        self.assertEqual(0, BaseNotification.objects.filter(object_id=ecju_query.id).count())

        # try to add document again
        self.add_query_document(case.id, ecju_query.id, status.HTTP_400_BAD_REQUEST)

    def test_exporter_cannot_delete_documents_of_closed_query(self):
        """Once a query is responded it is closed so ensure we cannot delete documents to closed queries"""
        case = self.create_standard_application_case(self.organisation)
        url = reverse("cases:case_ecju_queries", kwargs={"pk": case.id})
        data = {"question": "Please provide more details", "query_type": ECJUQueryType.ECJU}

        response = self.client.post(url, data, **self.gov_headers)
        response_data = response.json()
        ecju_query = EcjuQuery.objects.get(case=case)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response_data["ecju_query_id"], str(ecju_query.id))
        self.assertEqual("Please provide more details", ecju_query.question)
        self.assertIsNone(ecju_query.response)

        self.add_query_document(case.id, ecju_query.id, status.HTTP_201_CREATED)

        url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})
        data = {"response": "Additional details included"}
        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()["ecju_query"]
        self.assertEqual(response["response"], data["response"])
        self.assertEqual(len(response["documents"]), 1)

        url = reverse(
            "cases:case_ecju_query_document_detail",
            kwargs={"pk": case.id, "query_pk": ecju_query.id, "doc_pk": response["documents"][0]["id"]},
        )
        response = self.client.delete(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        self.assertIsNotNone(response["document"]["id"])


class ECJUQueriesChaserNotificationTests(DataTestClient):
    @freeze_time("2024-02-06 12:00:00")
    def setUp(self):
        super().setUp()
        # Require a valid formatted key else NotificationsAPIClient will complain with missing service id key.
        settings.GOV_NOTIFY_KEY = (
            "faketestkey-aa1539a1-0ba4-4ac2-b6ff-ae557aed2169-aa1539a1-0ba4-4ac2-b6ff-ae557aed2169"
        )
        self.case = self.create_standard_application_case(self.organisation)
        self.date_15_working_days_from_today = datetime.datetime(2024, 1, 16, 12, 00)

        self.ecju_query_case_1 = EcjuQueryFactory(
            question="ECJU Query 15 days",
            case=self.case,
            raised_by_user=self.gov_user,
            response=None,
            created_at=self.date_15_working_days_from_today,
            chaser_email_sent_on=self.date_15_working_days_from_today,
        )

    @freeze_time("2024-02-06 12:00:00")
    @override_settings(GOV_NOTIFY_ENABLED=True)
    @mock.patch("api.core.celery_tasks.NotificationsAPIClient.send_email_notification")
    def test_schedule_all_ecju_query_chaser_emails_filters(self, mock_gov_notification):
        EcjuQueryFactory(
            question="ECJU Query 14 days",
            case=self.case,
            raised_by_user=self.gov_user,
            created_at=datetime.datetime(2024, 1, 17, 12, 00),
        )

        ecju_quey_send_1 = EcjuQueryFactory(
            question="ECJU Query 15 days",
            case=self.case,
            raised_by_user=self.gov_user,
            created_at=self.date_15_working_days_from_today,
        )

        ecju_quey_send_2 = EcjuQueryFactory(
            question="ECJU Query reminder after 20 days",
            case=self.case,
            raised_by_user=self.gov_user,
            created_at=datetime.datetime(2024, 1, 9, 12, 00),
        )

        EcjuQueryFactory(
            question="ECJU Query reminder sent old",
            case=self.case,
            raised_by_user=self.gov_user,
            created_at=datetime.datetime(2024, 1, 17, 12, 00),
        )

        self.assertEqual(EcjuQuery.objects.filter(chaser_email_sent_on__isnull=True).count(), 4)

        schedule_all_ecju_query_chaser_emails.apply()
        self.assertEqual(mock_gov_notification.call_count, 2)

        self.assertEqual(EcjuQuery.objects.filter(chaser_email_sent_on__isnull=True).count(), 2)
        ecju_quey_send_1.refresh_from_db()
        ecju_quey_send_2.refresh_from_db()
        self.assertIsNotNone(ecju_quey_send_1.chaser_email_sent_on)
        self.assertIsNotNone(ecju_quey_send_2.chaser_email_sent_on)

    @freeze_time("2024-02-06 12:00:00")
    @mock.patch("api.core.celery_tasks.NotificationsAPIClient.send_email_notification")
    def test_schedule_all_ecju_query_chaser_emails_filters_terminal(self, mock_gov_notification):
        self.case.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        self.case.save()

        ecju_response_query = EcjuQueryFactory(
            question="Terminal Case 15 days",
            case=self.case,
            raised_by_user=self.gov_user,
            created_at=self.date_15_working_days_from_today,
        )

        schedule_all_ecju_query_chaser_emails.apply()
        mock_gov_notification.assert_not_called()

        ecju_response_query.refresh_from_db()
        self.assertIsNone(ecju_response_query.chaser_email_sent_on)

    @freeze_time("2024-02-06 12:00:00")
    @mock.patch("api.core.celery_tasks.NotificationsAPIClient.send_email_notification")
    def test_schedule_all_ecju_query_chaser_emails_filters_responded(self, mock_gov_notification):
        case_2 = self.create_standard_application_case(self.organisation)

        ecju_response_query = EcjuQueryFactory(
            question="ECJU Query 2 15 days",
            case=case_2,
            response="I have a response",
            raised_by_user=self.gov_user,
            responded_by_user=self.base_user,
            created_at=self.date_15_working_days_from_today,
        )

        schedule_all_ecju_query_chaser_emails.apply()
        mock_gov_notification.assert_not_called()

        ecju_response_query.refresh_from_db()
        self.assertIsNone(ecju_response_query.chaser_email_sent_on)

    @freeze_time("2024-02-06 12:00:00")
    @mock.patch("api.core.celery_tasks.NotificationsAPIClient.send_email_notification")
    def test_schedule_all_ecju_query_chaser_emails_filters_is_chaser_email_sent(self, mock_gov_notification):
        case_2 = self.create_standard_application_case(self.organisation)

        EcjuQueryFactory(
            question="ECJU Query 15 days",
            case=case_2,
            raised_by_user=self.gov_user,
            created_at=self.date_15_working_days_from_today,
            chaser_email_sent_on=datetime.datetime.now(),
        )

        schedule_all_ecju_query_chaser_emails.apply()
        mock_gov_notification.assert_not_called()

    @freeze_time("2024-02-06 12:00:00")
    @mock.patch("api.cases.notify.send_email")
    def test_schedule_all_ecju_query_chaser_emails_send_mail_params(self, mock_send_email):
        self.ecju_query_case_1.chaser_email_sent_on = None
        self.ecju_query_case_1.save()

        schedule_all_ecju_query_chaser_emails.apply()

        mock_send_email.assert_called_once()

        expected_payload = ExporterECJUQueryChaser(
            case_reference=self.case.reference_code,
            exporter_frontend_ecju_queries_url=get_exporter_frontend_url(f"/applications/{self.case.pk}/ecju-queries/"),
            remaining_days=5,
            open_working_days=15,
        )
        mock_send_email.assert_called_with(
            self.case.submitted_by.email,
            TemplateType.EXPORTER_ECJU_QUERY_CHASER,
            expected_payload,
            mark_ecju_query_as_sent.si(self.ecju_query_case_1.pk),
        )

    @freeze_time("2024-02-06 12:00:00")
    @override_settings(GOV_NOTIFY_ENABLED=True)
    @mock.patch("api.core.celery_tasks.NotificationsAPIClient.send_email_notification")
    def test_schedule_all_ecju_query_chaser_emails_callback_marks_sent(self, mock_gov_notification):
        self.ecju_query_case_1.chaser_email_sent_on = None
        self.ecju_query_case_1.save()

        schedule_all_ecju_query_chaser_emails.apply()

        mock_gov_notification.assert_called_once()

        self.ecju_query_case_1.refresh_from_db()

        self.assertIsNotNone(self.ecju_query_case_1.chaser_email_sent_on)

    @freeze_time("2024-02-06 12:00:00")
    @mock.patch("api.cases.celery_tasks.send_ecju_query_chaser_email.delay")
    def test_send_ecju_query_notifications_raises_exception(self, mock_send_ecju_query_chaser_email):
        self.ecju_query_case_1.chaser_email_sent_on = None
        self.ecju_query_case_1.save()

        mock_send_ecju_query_chaser_email.side_effect = Exception()
        with pytest.raises(Exception):
            schedule_all_ecju_query_chaser_emails()

        mock_send_ecju_query_chaser_email.assert_called_once()
        self.assertEqual(EcjuQuery.objects.filter(chaser_email_sent_on__isnull=False).count(), 0)

    @freeze_time("2024-02-06 12:00:00")
    @mock.patch("api.cases.notify.send_email")
    @mock.patch("api.cases.notify._notify_exporter_ecju_query_chaser")
    def test_send_ecju_query_chaser_email_raises_exception(self, mock_notify_chaser_email, mock_send_email):
        self.ecju_query_case_1.chaser_email_sent_on = None
        self.ecju_query_case_1.save()

        mock_notify_chaser_email.side_effect = Exception()

        with pytest.raises(Exception):
            send_ecju_query_chaser_email(self.ecju_query_case_1.pk)
        mock_send_email.assert_not_called()
        self.ecju_query_case_1.refresh_from_db()
        self.assertIsNone(self.ecju_query_case_1.chaser_email_sent_on)

    @freeze_time("2024-02-06 12:00:00")
    def test_mark_ecju_query_as_sent(self):
        self.ecju_query_case_1.chaser_email_sent_on = None
        self.ecju_query_case_1.save_base()

        self.assertIsNone(self.ecju_query_case_1.responded_at)

        mark_ecju_query_as_sent(self.ecju_query_case_1.pk)

        self.ecju_query_case_1.refresh_from_db()
        self.assertIsNotNone(self.ecju_query_case_1.chaser_email_sent_on)
        # Need to esnure responded_at is not impacted auto_now_add and save business logic shouldn't be executed
        self.assertIsNone(self.ecju_query_case_1.responded_at)

    @parameterized.expand(["this is some response text", ""])
    def test_exporter_responding_to_query_creates_case_note_mention_for_caseworker(self, response_text):
        case = self.create_standard_application_case(self.organisation)

        # caseworker raises a query
        url = reverse("cases:case_ecju_queries", kwargs={"pk": case.id})
        question_text = "this is the question text"
        data = {"question": question_text, "query_type": ECJUQueryType.ECJU}

        response = self.client.post(url, data, **self.gov_headers)
        response_data = response.json()
        ecju_query = EcjuQuery.objects.get(case=case)

        self.assertFalse(ecju_query.is_query_closed)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response_data["ecju_query_id"], str(ecju_query.id))
        self.assertEqual(question_text, ecju_query.question)
        self.assertIsNone(ecju_query.response)

        # exporter responds to the query
        url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})
        data = {"response": response_text}

        response = self.client.put(url, data, **self.exporter_headers)
        ecju_query = EcjuQuery.objects.get(case=case)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(ecju_query.is_query_closed)

        # check case note mention is created
        case_note_mentions = CaseNoteMentions.objects.first()
        case_note = case_note_mentions.case_note
        audit_object = Audit.objects.first()

        expected_gov_user = ecju_query.raised_by_user
        expected_exporter_user = ecju_query.responded_by_user
        expected_mention_users_text = f"{expected_gov_user.full_name} ({expected_gov_user.team.name})"
        expected_case_note_text = f"{expected_exporter_user.get_full_name()} has responded to a query."
        expected_audit_payload = {
            "mention_users": [expected_mention_users_text],
            "additional_text": expected_case_note_text,
        }

        self.assertEqual(case_note_mentions.user, expected_gov_user)
        self.assertEqual(case_note.text, expected_case_note_text)
        self.assertEqual(audit_object.payload, expected_audit_payload)
        self.assertEqual(audit_object.payload["additional_text"], expected_case_note_text)
