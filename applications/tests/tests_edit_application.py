from django.urls import reverse
from rest_framework import status

from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status_enum
from test_helpers.clients import DataTestClient


class EditApplicationTests(DataTestClient):

    def setUp(self):
        super().setUp()

    def test_edit_application_name(self):
        application = self.create_standard_application(self.organisation)
        url = reverse('applications:application', kwargs={'pk': application.id})
        original_last_modified_at = application.last_modified_at

        data = {'name': 'new app name!'}

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.name, data['name'])
        self.assertNotEqual(application.last_modified_at, original_last_modified_at)

    def test_edit_submitted_application_name(self):
        application = self.create_standard_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_from_status_enum(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse('applications:application', kwargs={'pk': application.id})
        original_last_modified_at = application.last_modified_at

        data = {'name': 'new app name!'}

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.name, data['name'])
        self.assertNotEqual(application.last_modified_at, original_last_modified_at)

    def test_edit_application_reference_number(self):
        application = self.create_standard_application(self.organisation)
        self.submit_application(application)
        application.status = get_case_status_from_status_enum(CaseStatusEnum.APPLICANT_EDITING)
        application.save()
        url = reverse('applications:application', kwargs={'pk': application.id})
        original_last_modified_at = application.last_modified_at

        data = {'reference_number_on_information_form': '35236246'}

        response = self.client.put(url, data, **self.exporter_headers)

        application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(application.reference_number_on_information_form,
                         data['reference_number_on_information_form'])
        self.assertNotEqual(application.last_modified_at, original_last_modified_at)
