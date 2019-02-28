from django.test import TestCase

# Create your tests here.

from django.test import TestCase, Client

# I want this test to assert that when an incomplete application is submitted (via GET/POST to submit_application?)
# it returns a response about the missing data, doing this test driven so haven't created the necessary views yet
from .models import FormComplete
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
