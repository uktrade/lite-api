from django.test import TestCase

# Create your tests here.

from django.test import TestCase, Client

# I want this test to assert that when an incomplete application is submitted (via GET/POST to submit_application?)
# it returns a response about the missing data, doing this test driven so haven't created the necessary views yet

from drafts import Draft

class ApplicationTests(TestCase):

    def test_reject_submit_if_data_is_missing(self):
        incomplete_draft = Draft()
        
        assert equals(response.status, "422")