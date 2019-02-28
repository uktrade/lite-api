import json

from django.test import TestCase, Client

from .models import FormComplete, Application
from drafts.models import Draft


class ApplicationTests(TestCase):

    def test_reject_submit_if_usage_data_is_missing(self):
        incomplete_draft = Draft()
        incomplete_draft.control_code = "ML2"
        incomplete_draft.destination = "Poland"
        incomplete_draft.activity = "Trade"
        self.assertEqual(FormComplete(incomplete_draft).usage, "Usage cannot be blank")
        self.assertEqual(FormComplete(incomplete_draft).ready_for_submission, False)

    def test_reject_submit_if_activity_data_is_missing(self):
        incomplete_draft = Draft()
        incomplete_draft.control_code = "ML2"
        incomplete_draft.destination = "Poland"
        incomplete_draft.usage = "some purpose"
        self.assertEqual(FormComplete(incomplete_draft).activity, "Activity cannot be blank")
        self.assertEqual(FormComplete(incomplete_draft).ready_for_submission, False)

    def test_reject_submit_if_destination_data_is_missing(self):
        incomplete_draft = Draft()
        incomplete_draft.control_code = "ML2"
        incomplete_draft.activity = "Trade"
        incomplete_draft.usage = "some purpose"
        self.assertEqual(FormComplete(incomplete_draft).destination, "Destination cannot be blank")
        self.assertEqual(FormComplete(incomplete_draft).ready_for_submission, False)

    def test_reject_submit_if_control_code_data_is_missing(self):
        incomplete_draft = Draft()
        incomplete_draft.destination = "Poland"
        incomplete_draft.activity = "Trade"
        incomplete_draft.usage = "some purpose"
        self.assertEqual(FormComplete(incomplete_draft).control_code, "Control code cannot be blank")
        self.assertEqual(FormComplete(incomplete_draft).ready_for_submission, False)

    def test_accept_submit_if_form_is_ready_for_submission(self):
        complete_draft = Draft
        complete_draft.control_code = "ML2"
        complete_draft.destination = "Poland"
        complete_draft.activity = "Trade"
        complete_draft.usage = "Fun"
        self.assertEqual(FormComplete(complete_draft).ready_for_submission, True)

    def test_reject_submit_if_all_fields_missing(self):
        empty_draft = Draft()
        self.assertEqual(FormComplete(empty_draft).control_code, "Control code cannot be blank")
        self.assertEqual(FormComplete(empty_draft).destination, "Destination cannot be blank")
        self.assertEqual(FormComplete(empty_draft).activity, "Activity cannot be blank")
        self.assertEqual(FormComplete(empty_draft).usage, "Usage cannot be blank")
        self.assertEqual(FormComplete(empty_draft).ready_for_submission, False)


    def test_application_successful_submit(self):
        complete_draft = Draft()
        complete_draft.id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"
        complete_draft.control_code = "ML2"
        complete_draft.destination = "Poland"
        complete_draft.activity = "Trade"
        complete_draft.usage = "Fun"
        complete_draft.save()

        client = Client()
        response = client.post('/applications/', {'id': '90D6C724-0339-425A-99D2-9D2B8E864EC7'})

        self.assertEqual(response.status_code, 201)

        self.assertEqual(len(Draft.objects.filter(id="90D6C724-0339-425A-99D2-9D2B8E864EC7")), 0)
        self.assertEqual(Application.objects.get(id="90D6C724-0339-425A-99D2-9D2B8E864EC7").destination, "Poland")

    def test_application_unsuccessful_submit_empty_form(self):
        empty_draft = Draft()
        empty_draft.id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"
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

