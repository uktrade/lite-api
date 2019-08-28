from django.urls import reverse
from rest_framework import status

from cases.models import Case
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class CaseActivityTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = Case.objects.get(application=self.standard_application)
        self.url = reverse('cases:activity', kwargs={'pk': self.case.id})

    def test_view_case_activity(self):
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['activity']), 0)

        # Add a case note
        self.create_case_note(self.case, 'Example Note', self.gov_user)

        # Validate that there is now one object in activity
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['activity']), 1)

        # Update the application status
        data = {
            'status': CaseStatusEnum.MORE_INFORMATION_REQUIRED,
        }

        self.client.put(reverse('applications:application', kwargs={'pk': self.standard_application.id}),
                        data=data, **self.gov_headers)

        # Validate that there are now two objects in activity
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['activity']), 2)
