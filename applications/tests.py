import json
from rest_framework import status
from django.test import TestCase, Client
from drafts.models import Draft
from applications.models import Application, FormComplete


class ApplicationTests(TestCase):

    # Creation

    def test_create_application(self):
        """
            Ensure we can create a new draft object.
            """
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        complete_draft = Draft(id=draft_id,
                               user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")
        complete_draft.save()

        url = '/applications/'
        data = {'id': draft_id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(Draft.objects.filter(id=draft_id)), 0)
        self.assertEqual(Application.objects.get(id=draft_id).destination, "Poland")

    def test_create_application_with_invalid_id(self):
        """
            Ensure we cannot create a new application object with an invalid draft id.
            """
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        complete_draft = Draft(id=draft_id,
                               user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")
        complete_draft.save()

        url = '/applications/'
        data = {'id': "90D6C724-0339-425A-99D2-9D2B8E864EC6"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(Draft.objects.filter(id=draft_id)), 1)

    def test_create_application_without_id(self):
        """
            Ensure we cannot create a new application object without a draft id.
            """
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        complete_draft = Draft(id=draft_id,
                               user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")
        complete_draft.save()

        url = '/applications/'
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(Draft.objects.filter(id=draft_id)), 1)

    def test_reject_submit_if_usage_data_is_missing(self):
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        incomplete_draft = Draft(id=draft_id,
                                 user_id="12345",
                                 control_code="ML2",
                                 destination="Poland",
                                 activity="Trade")

        self.assertEqual(FormComplete(incomplete_draft).usage, "Usage cannot be blank")
        self.assertEqual(FormComplete(incomplete_draft).ready_for_submission, False)

    def test_reject_submit_if_activity_data_is_missing(self):
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        incomplete_draft = Draft(id=draft_id,
                                 user_id="12345",
                                 control_code="ML2",
                                 destination="Poland",
                                 usage="Fun")

        self.assertEqual(FormComplete(incomplete_draft).activity, "Activity cannot be blank")
        self.assertEqual(FormComplete(incomplete_draft).ready_for_submission, False)

    def test_reject_submit_if_destination_data_is_missing(self):
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        incomplete_draft = Draft(id=draft_id,
                                 user_id="12345",
                                 control_code="ML2",
                                 activity="Trade",
                                 usage="Fun")

        self.assertEqual(FormComplete(incomplete_draft).destination, "Destination cannot be blank")
        self.assertEqual(FormComplete(incomplete_draft).ready_for_submission, False)

    def test_reject_submit_if_control_code_data_is_missing(self):
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        incomplete_draft = Draft(id=draft_id,
                                 user_id="12345",
                                 destination="Poland",
                                 activity="Trade",
                                 usage="Fun")

        self.assertEqual(FormComplete(incomplete_draft).control_code, "Control code cannot be blank")
        self.assertEqual(FormComplete(incomplete_draft).ready_for_submission, False)

    def test_accept_submit_if_form_is_ready_for_submission(self):
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        complete_draft = Draft(id=draft_id,
                               user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")

        self.assertEqual(FormComplete(complete_draft).ready_for_submission, True)

    def test_reject_submit_if_all_fields_missing(self):
        empty_draft = Draft()
        self.assertEqual(FormComplete(empty_draft).control_code, "Control code cannot be blank")
        self.assertEqual(FormComplete(empty_draft).destination, "Destination cannot be blank")
        self.assertEqual(FormComplete(empty_draft).activity, "Activity cannot be blank")
        self.assertEqual(FormComplete(empty_draft).usage, "Usage cannot be blank")
        self.assertEqual(FormComplete(empty_draft).ready_for_submission, False)


    def test_application_successful_submit(self):
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        complete_draft = Draft(id=draft_id,
                               user_id="12345",
                               control_code="ML2",
                               destination="Poland",
                               activity="Trade",
                               usage="Fun")

        complete_draft.save()

        client = Client()
        response = client.post('/applications/', {'id': '90D6C724-0339-425A-99D2-9D2B8E864EC7'})

        self.assertEqual(response.status_code, 201)

        self.assertEqual(len(Draft.objects.filter(id="90D6C724-0339-425A-99D2-9D2B8E864EC7")), 0)
        self.assertEqual(Application.objects.get(id="90D6C724-0339-425A-99D2-9D2B8E864EC7").destination, "Poland")

    def test_application_unsuccessful_submit_empty_form(self):
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"

        empty_draft = Draft(id=draft_id,
                            user_id="12345")

        empty_draft.save()

        client = Client()
        response = client.post('/applications/', {'id': "90D6C724-0339-425A-99D2-9D2B8E864EC7"})

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.content)

        self.assertEqual(data["control_code"], "Control code cannot be blank")
        self.assertEqual(data["activity"], "Activity cannot be blank")
        self.assertEqual(data["destination"], "Destination cannot be blank")
        self.assertEqual(data["usage"], "Usage cannot be blank")

    def test_application_unsuccessful_submit_invalid_id(self):
        client = Client()
        response = client.post('/applications/', {'id': "90D6C724-0339-425A-99D2-9D2B8E864EC9"})

        self.assertEqual(response.status_code, 404)

    def test_application_submit_invalid_methods(self):
        client = Client()

        response = client.get('/applications/')
        self.assertEqual(response.status_code, 405)

        response = client.put('/applications/')
        self.assertEqual(response.status_code, 405)

        response = client.delete('/applications/')
        self.assertEqual(response.status_code, 405)
