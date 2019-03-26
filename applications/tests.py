from rest_framework import status
from django.test import TestCase
from applications.models import Application
from applications.libraries.ValidateFormFields import ValidateFormFields


class ApplicationTests(TestCase):

    # Creation

    def test_create_application(self):
        """
            Ensure we can create a new draft object.
            """
        draft_id = '90D6C724-0339-425A-99D2-9D2B8E864EC7'
        complete_draft = Application(id=draft_id,
                                     user_id='12345',
                                     control_code='ML2',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     usage='Fun',
                                     draft=True)
        complete_draft.save()

        url = '/applications/'
        data = {'id': draft_id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.get(pk=draft_id).draft, False)

    def test_create_application_with_invalid_id(self):
        """
            Ensure we cannot create a new application object with an invalid draft id.
            """
        draft_id = '90D6C724-0339-425A-99D2-9D2B8E864EC7'
        complete_draft = Application(id=draft_id,
                                     user_id='12345',
                                     control_code='ML2',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     usage='Fun',
                                     draft=True)
        complete_draft.save()

        url = '/applications/'
        data = {'id': '90D6C724-0339-425A-99D2-9D2B8E864EC6'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Application.objects.get(pk=draft_id).draft, True)

    def test_create_application_without_id(self):
        """
            Ensure we cannot create a new application object without a draft id.
            """
        complete_draft = Application(id='90D6C724-0339-425A-99D2-9D2B8E864EC7',
                                     user_id='12345',
                                     control_code='ML2',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     usage='Fun',
                                     draft=True)
        complete_draft.save()

        url = '/applications/'
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(Application.objects.filter(id='90D6C724-0339-425A-99D2-9D2B8E864EC7')), 1)

    def test_reject_submit_if_usage_data_is_missing(self):
        incomplete_draft = Application(id='90D6C724-0339-425A-99D2-9D2B8E864EC7',
                                       user_id='12345',
                                       control_code='ML2',
                                       name='Test',
                                       destination='Poland',
                                       activity='Trade',
                                       draft=True)

        self.assertEqual(ValidateFormFields(incomplete_draft).usage, "Usage cannot be blank")
        self.assertEqual(ValidateFormFields(incomplete_draft).ready_for_submission, False)

    def test_reject_submit_if_activity_data_is_missing(self):
        incomplete_draft = Application(id='90D6C724-0339-425A-99D2-9D2B8E864EC7',
                                       user_id='12345',
                                       control_code='ML2',
                                       name='Test',
                                       destination='Poland',
                                       draft=True)

        self.assertEqual(ValidateFormFields(incomplete_draft).activity, "Activity cannot be blank")
        self.assertEqual(ValidateFormFields(incomplete_draft).ready_for_submission, False)

    def test_reject_submit_if_destination_data_is_missing(self):
        incomplete_draft = Application(id='90D6C724-0339-425A-99D2-9D2B8E864EC7',
                                       user_id='12345',
                                       control_code='ML2',
                                       name='Test',
                                       activity='Trade',
                                       draft=True)

        self.assertEqual(ValidateFormFields(incomplete_draft).destination, "Destination cannot be blank")
        self.assertEqual(ValidateFormFields(incomplete_draft).ready_for_submission, False)

    def test_reject_submit_if_control_code_data_is_missing(self):
        incomplete_draft = Application(id='90D6C724-0339-425A-99D2-9D2B8E864EC7',
                                       user_id='12345',
                                       name='Test',
                                       destination='Poland',
                                       activity='Trade',
                                       draft=True)

        self.assertEqual(ValidateFormFields(incomplete_draft).control_code, "Control code cannot be blank")
        self.assertEqual(ValidateFormFields(incomplete_draft).ready_for_submission, False)

    def test_accept_submit_if_form_is_ready_for_submission(self):
        complete_draft = Application(id='90D6C724-0339-425A-99D2-9D2B8E864EC7',
                                     user_id='12345',
                                     control_code='ML2',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     draft=True)

        self.assertEqual(ValidateFormFields(complete_draft).ready_for_submission, True)

    def test_reject_submit_if_all_fields_missing(self):
        empty_draft = Application()
        self.assertEqual(ValidateFormFields(empty_draft).control_code, 'Control code cannot be blank')
        self.assertEqual(ValidateFormFields(empty_draft).destination, 'Destination cannot be blank')
        self.assertEqual(ValidateFormFields(empty_draft).activity, 'Activity cannot be blank')
        self.assertEqual(ValidateFormFields(empty_draft).usage, 'Usage cannot be blank')
        self.assertEqual(ValidateFormFields(empty_draft).ready_for_submission, False)
