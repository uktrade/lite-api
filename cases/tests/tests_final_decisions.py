from django.urls import reverse
from rest_framework import status

from cases.models import Case
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient
from users.models import Role, Permission


class CaseActivityTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application', self.test_helper.organisation)
        self.application = self.submit_draft(self.draft)
        self.case = Case.objects.get(application=self.application)
        self.url = reverse('cases:activity', kwargs={'pk': self.case.id})

    def test_cannot_make_final_decision_without_permission(self):
        data = {
            'status': CaseStatusEnum.APPROVED,
        }

        response = self.client.put(reverse('applications:application', kwargs={'pk': self.application.id}), data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def tests_can_record_final_decision_with_correct_permissions(self):
        role = Role(name='some')
        role.permissions.set([Permission.objects.get(id='MAKE_FINAL_DECISIONS').id])
        role.save()
        self.gov_user.role = role
        self.gov_user.save()

        data = {
            'status': CaseStatusEnum.APPROVED,
        }

        response = self.client.put(reverse('applications:application', kwargs={'pk': self.application.id}), data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
