from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy
from parameterized import parameterized
from rest_framework import status

from test_helpers.clients import DataTestClient

from api.cases.enums import CaseTypeEnum
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.models import CaseNote, EcjuQuery
from api.f680.tests.factories import SubmittedF680ApplicationFactory
from api.users.libraries.user_to_token import user_to_token
from api.users.models import ExporterNotification


class ExporterUserNotificationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case_note_content_type = ContentType.objects.get_for_model(CaseNote)
        self.ecju_query_content_type = ContentType.objects.get_for_model(EcjuQuery)
        self.generated_case_doc_content_type = ContentType.objects.get_for_model(GeneratedCaseDocument)
        self.url = reverse_lazy("users:notifications")

    def _create_application_with_notifications(self):
        application = self.create_standard_application_case(self.organisation)
        self.create_case_note(application, "This is a test note 1", self.gov_user.baseuser_ptr, True)
        self.create_case_note(application, "This is a test note 2", self.gov_user.baseuser_ptr, False)
        self.create_ecju_query(application, "This is an ecju query")
        self.create_generated_case_document(
            application,
            template=self.create_letter_template(case_types=[CaseTypeEnum.SIEL.id]),
        )
        return application

    def _create_f680_clearance_with_notifications(self):
        application = SubmittedF680ApplicationFactory(organisation=self.organisation)
        self.create_case_note(application, "This is a test note 1", self.gov_user.baseuser_ptr, True)
        self.create_case_note(application, "This is a test note 2", self.gov_user.baseuser_ptr, False)
        self.create_ecju_query(application, "This is an ecju query")
        self.create_generated_case_document(
            application,
            template=self.create_letter_template(case_types=[CaseTypeEnum.F680.id]),
        )
        return application

    @parameterized.expand(
        [
            [_create_application_with_notifications],
            [_create_f680_clearance_with_notifications],
        ]
    )
    def test_create_case_notifications_success(self, create_case_func):
        case = create_case_func(self)

        case_notification_count = ExporterNotification.objects.filter(
            user_id=self.exporter_user.pk,
            organisation=self.exporter_user.organisation,
            case=case,
        ).count()
        case_case_note_notification_count = ExporterNotification.objects.filter(
            user_id=self.exporter_user.pk,
            organisation=self.exporter_user.organisation,
            content_type=self.case_note_content_type,
            case=case,
        ).count()
        case_ecju_query_notification_count = ExporterNotification.objects.filter(
            user_id=self.exporter_user.pk,
            organisation=self.exporter_user.organisation,
            content_type=self.ecju_query_content_type,
            case=case,
        ).count()
        case_generated_case_document_notification_count = ExporterNotification.objects.filter(
            user_id=self.exporter_user.pk,
            organisation=self.exporter_user.organisation,
            content_type=self.generated_case_doc_content_type,
            case=case,
        ).count()

        self.assertEqual(case_notification_count, 3)
        self.assertEqual(case_case_note_notification_count, 1)
        self.assertEqual(case_ecju_query_notification_count, 1)
        self.assertEqual(case_generated_case_document_notification_count, 1)

    def test_get_notifications_for_user_success(self):
        self._create_application_with_notifications()
        self._create_f680_clearance_with_notifications()

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # This is three because the two ecju queries don't send out a
        # notification each
        self.assertEqual(
            response_data["notifications"],
            {
                "application": 3,
                "security_clearance": 3,
            },
        )

    def test_get_notifications_for_user_in_multiple_orgs_success(self):
        """
        Given an exporter user in multiple orgs
        When an API user gets notifications for the exporter user and one of their orgs
        Then only the notifications specific to that user and org combination are returned
        """
        self._create_application_with_notifications()

        org_2, _ = self.create_organisation_with_exporter_user("Org 2")
        self.add_exporter_user_to_org(org_2, self.exporter_user)
        self.exporter_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(self.exporter_user.baseuser_ptr),
            "HTTP_ORGANISATION_ID": str(org_2.id),
        }
        application = self.create_standard_application_case(org_2)
        self.create_case_note(application, "This is a test note 3", self.gov_user.baseuser_ptr, True)
        self.create_ecju_query(application, "This is an ecju query")

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["notifications"]["application"], 2)
        # Check that the 2 notifications we got are only for ones created while org_2 is the currently selected org
        self.assertEqual(
            response_data["notifications"]["application"],
            ExporterNotification.objects.filter(user_id=self.exporter_user.pk, organisation=org_2).count(),
        )
        self.assertNotEqual(
            ExporterNotification.objects.filter(user_id=self.exporter_user.pk).count(),
            ExporterNotification.objects.filter(user_id=self.exporter_user.pk, organisation=org_2).count(),
        )

    def test_get_applications_with_notifications_success(self):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        self._create_application_with_notifications()

        response = self.client.get(reverse_lazy("applications:applications"), **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application_response_data = response.json()["results"][0]
        self.assertIn("exporter_user_notification_count", application_response_data)
        self.assertEqual(application_response_data["exporter_user_notification_count"], 3)

    def test_get_application_with_notifications_success(self):
        case = self._create_application_with_notifications()

        response = self.client.get(
            reverse_lazy("applications:application", kwargs={"pk": str(case.id)}), **self.exporter_headers
        )
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("exporter_user_notification_count", response_data)
        self.assertEqual(len(response_data["exporter_user_notification_count"]), 3)
