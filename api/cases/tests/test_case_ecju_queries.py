from unittest import mock

from django.urls import reverse
from django.utils import timezone
from faker import Faker
from parameterized import parameterized
from rest_framework import status

from api.applications.models import BaseApplication
from api.cases.enums import ECJUQueryType
from api.cases.models import EcjuQuery
from api.compliance.tests.factories import ComplianceSiteCaseFactory, ComplianceVisitCaseFactory
from api.licences.enums import LicenceStatus
from api.picklists.enums import PicklistType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from api.users.tests.factories import ExporterUserFactory

faker = Faker()


class ECJUQueriesViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.case2 = self.create_standard_application_case(self.organisation)
        self.no_ecju_queries_case = self.create_standard_application_case(self.organisation)

        self.url = reverse("cases:case_ecju_queries", kwargs={"pk": self.case.id})

        ecju_query = EcjuQuery(question="ECJU Query 1", case=self.case, raised_by_user=self.gov_user)
        ecju_query.save()

        self.team_2 = self.create_team("TAU")
        self.gov_user2_email = "bob@slob.com"
        self.gov_user_2 = self.create_gov_user(self.gov_user2_email, self.team_2)

        ecju_query = EcjuQuery(
            question="ECJU Query 2",
            case=self.case,
            response="I have a response",
            raised_by_user=self.gov_user_2,
            responded_by_user=self.exporter_user,
            query_type=PicklistType.ECJU,
        )
        ecju_query.save()
        ecju_query = EcjuQuery(question="ECJU Query 3", case=self.case2, raised_by_user=self.gov_user)
        ecju_query.save()

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
        self.assertEqual(returned_ecju_query_1.get("team")["name"], "Admin")
        # We can't predict exactly when the query is created so we settle for the fact that its set
        self.assertIsNotNone(returned_ecju_query_1.get("created_at"))

        returned_ecju_query_2 = response_json.get("ecju_queries")[1]
        self.assertEqual(returned_ecju_query_2.get("question"), "ECJU Query 2")
        self.assertEqual(returned_ecju_query_2.get("response"), "I have a response")
        self.assertEqual(returned_ecju_query_2.get("team")["name"], "TAU")
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
        ecju_query = EcjuQuery(question="Ble", case=case, raised_by_user=self.gov_user)
        ecju_query.save()

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


class ECJUQueriesCreateTest(DataTestClient):
    @parameterized.expand([ECJUQueryType.ECJU, ECJUQueryType.PRE_VISIT_QUESTIONNAIRE, ECJUQueryType.COMPLIANCE_ACTIONS])
    def test_gov_user_can_create_ecju_queries(self, query_type):
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


class ECJUQueriesComplianceCreateTest(DataTestClient):
    def setUp(self):
        super().setUp()
        self.compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        self.create_licence(self.create_open_application_case(self.organisation), status=LicenceStatus.ISSUED)

        application = self.create_open_application_case(self.organisation)
        application.submitted_by = ExporterUserFactory()
        application.save()
        self.create_licence(application, status=LicenceStatus.ISSUED)
        self.data = {"question": "Test ECJU Query question?", "query_type": PicklistType.PRE_VISIT_QUESTIONNAIRE}

    @mock.patch("gov_notify.service.client")
    def test_query_sends_email_to_each_application_submitter(self, mock_client):
        """
        When a GOV user submits a valid query to a compliance case
        Then the request is successful and the query is saved
        And an email is sent to each user that submitted a valid application
        on that site which has a licence
        """
        url = reverse("cases:case_ecju_queries", kwargs={"pk": self.compliance_case.id})

        response = self.client.post(url, self.data, **self.gov_headers)
        response_data = response.json()
        ecju_query = EcjuQuery.objects.get()

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response_data["ecju_query_id"], str(ecju_query.id))
        self.assertEqual(ecju_query.question, self.data["question"])
        self.assertEqual(mock_client.send_email.call_count, 2)

    @mock.patch("gov_notify.service.client")
    def test_query_sends_email_to_each_application_submitter_site(self, mock_client):
        """
        When a GOV user submits a valid query to a compliance visit case
        Then the request is successful and the query is saved
        And an email is sent to each user that submitted a valid application
        on that site which has a licence
        """
        compliance_site_case = ComplianceVisitCaseFactory(
            site_case=self.compliance_case,
            organisation=self.organisation,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        url = reverse("cases:case_ecju_queries", kwargs={"pk": compliance_site_case.id})

        response = self.client.post(url, self.data, **self.gov_headers)
        response_data = response.json()
        ecju_query = EcjuQuery.objects.get()

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response_data["ecju_query_id"], str(ecju_query.id))
        self.assertEqual(ecju_query.question, self.data["question"])
        self.assertEqual(mock_client.send_email.call_count, 2)

    @mock.patch("gov_notify.service.client")
    def test_query_sends_email_to_each_application_submitter_no_duplicates(self, mock_client):
        """
        When a GOV user submits a valid query to a compliance case
        Then the request is successful and the query is saved
        And an email is sent to each user that submitted a valid application
        on that site which has a licence, without duplicates
        """
        for application in BaseApplication.objects.all():
            application.submitted_by = self.exporter_user
            application.save()
        url = reverse("cases:case_ecju_queries", kwargs={"pk": self.compliance_case.id})

        response = self.client.post(url, self.data, **self.gov_headers)
        response_data = response.json()
        ecju_query = EcjuQuery.objects.get()

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response_data["ecju_query_id"], str(ecju_query.id))
        self.assertEqual(ecju_query.question, self.data["question"])
        self.assertEqual(mock_client.send_email.call_count, 1)


class ECJUQueriesResponseTests(DataTestClient):
    @mock.patch("api.documents.tasks.scan_document_for_viruses.now")
    def add_query_document(self, case_id, query_id, expected_status, doc_virus_scan_task):
        doc_virus_scan_task.return_value = None
        url = reverse("cases:case_ecju_query_add_document", kwargs={"pk": case_id, "query_pk": query_id})
        file_name = faker.file_name()
        data = {
            "name": file_name,
            "s3_key": f"{file_name}_{faker.uuid4()}",
            "description": faker.text(),
            "size": 1 << 10,
            "virus_scanned_at": timezone.now(),
        }
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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = response.json()["ecju_query"]
        self.assertEqual(response["response"], data["response"])

        if add_documents:
            self.assertEqual(len(response["documents"]), len(documents_to_be_added))

    @parameterized.expand([ECJUQueryType.ECJU, ECJUQueryType.PRE_VISIT_QUESTIONNAIRE, ECJUQueryType.COMPLIANCE_ACTIONS])
    def test_exporter_responds_to_query(self, query_type):
        """Respond to queries without and with adding documents"""
        self._test_exporter_responds_to_query(False, query_type)
        self._test_exporter_responds_to_query(True, query_type)

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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
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

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response_data["ecju_query_id"], str(ecju_query.id))
        self.assertEqual("Please provide required documents", ecju_query.question)
        self.assertIsNone(ecju_query.response)

        self.add_query_document(case.id, ecju_query.id, status.HTTP_201_CREATED)

        query_response_url = reverse("cases:case_ecju_query", kwargs={"pk": case.id, "ecju_pk": ecju_query.id})
        data = {"response": "Attached the requested documents"}
        response = self.client.put(query_response_url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = response.json()["ecju_query"]
        self.assertEqual(response["response"], data["response"])
        self.assertEqual(len(response["documents"]), 1)

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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
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
