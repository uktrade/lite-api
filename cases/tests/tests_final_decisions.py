from django.urls import reverse
from rest_framework import status

from cases.models import Case
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient
from users.models import Role, Permission


class CaseActivityTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = Case.objects.get(application=self.standard_application)
        self.url = reverse('cases:activity', kwargs={'pk': self.case.id})

    def test_cannot_make_final_decision_without_permission(self):
        data = {
            'status': CaseStatusEnum.FINALISED,
        }

        response = self.client.put(reverse('applications:manage_status', kwargs={'pk': self.standard_application.id}),
                                   data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_record_final_decision_with_correct_permissions(self):
        role = Role(name='some')
        role.permissions.set([Permission.objects.get(id='MANAGE_FINAL_ADVICE').id])
        role.save()
        self.gov_user.role = role
        self.gov_user.save()

        data = {
            'status': CaseStatusEnum.FINALISED,
        }

        response = self.client.put(reverse('applications:manage_status', kwargs={'pk': self.standard_application.id}),
                                   data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
