from django.urls import path, include, reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from applications.models import Application
from applications.libraries.ValidateFormFields import ValidateFormFields
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ApplicationsTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient()

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_create_application_without_id(self):
        """
            Ensure we cannot create a new application object without a draft id.
        """
        complete_draft = Application(id='90D6C724-0339-425A-99D2-9D2B8E864EC7',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     usage='Fun')
        complete_draft.save()

        url = reverse('applications:applications')
        response = self.client.post(url, {}, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(Application.objects.filter(id='90D6C724-0339-425A-99D2-9D2B8E864EC7')), 1)

    def test_reject_submit_if_usage_data_is_missing(self):
        incomplete_draft = Application(id='90D6C724-0339-425A-99D2-9D2B8E864EC7',
                                       name='Test',
                                       destination='Poland',
                                       activity='Trade')

        self.assertEqual(ValidateFormFields(incomplete_draft).usage, "Usage cannot be blank")
        self.assertEqual(ValidateFormFields(incomplete_draft).ready_for_submission, False)

    def test_reject_submit_if_activity_data_is_missing(self):
        incomplete_draft = Application(id='90D6C724-0339-425A-99D2-9D2B8E864EC7',
                                       name='Test',
                                       destination='Poland')

        self.assertEqual(ValidateFormFields(incomplete_draft).activity, "Activity cannot be blank")
        self.assertEqual(ValidateFormFields(incomplete_draft).ready_for_submission, False)

    def test_reject_submit_if_destination_data_is_missing(self):
        incomplete_draft = Application(id='90D6C724-0339-425A-99D2-9D2B8E864EC7',
                                       name='Test',
                                       activity='Trade')

        self.assertEqual(ValidateFormFields(incomplete_draft).destination, "Destination cannot be blank")
        self.assertEqual(ValidateFormFields(incomplete_draft).ready_for_submission, False)

    def test_accept_submit_if_form_is_ready_for_submission(self):
        complete_draft = Application(id='90D6C724-0339-425A-99D2-9D2B8E864EC7',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     usage='Trade')

        self.assertEqual(ValidateFormFields(complete_draft).ready_for_submission, True)

    def test_reject_submit_if_all_fields_missing(self):
        empty_draft = Application()
        self.assertEqual(ValidateFormFields(empty_draft).destination, 'Destination cannot be blank')
        self.assertEqual(ValidateFormFields(empty_draft).activity, 'Activity cannot be blank')
        self.assertEqual(ValidateFormFields(empty_draft).usage, 'Usage cannot be blank')
        self.assertEqual(ValidateFormFields(empty_draft).ready_for_submission, False)
