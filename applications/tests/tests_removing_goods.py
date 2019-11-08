from django.urls import reverse
from rest_framework import status

from applications.models import GoodOnApplication
from goods.enums import GoodStatus
from goods.models import Good
from static.statuses.libraries.get_case_status import get_case_status_by_status
from applications.libraries.case_status_helpers import get_case_statuses
from static.units.enums import Units
from test_helpers.clients import DataTestClient
from users.libraries.user_to_token import user_to_token
from users.models import UserOrganisationRelationship
from parameterized import parameterized


class RemovingGoodsOffDraftsTests(DataTestClient):

    def test_remove_a_good_from_draft_success(self):
        """
        Given a standard application with a good
        And the good's status is SUBMITTED
        And there are no other applications with this good attached
        When I attempt to delete the good from the application
        Then the good_on_application is deleted
        And the good status is changed to DRAFT
        """
        draft = self.create_standard_application(self.organisation)
        self.submit_application(draft) # This will submit the application and set the good status to SUBMITTED

        url = reverse('applications:good_on_application',
                      kwargs={'good_on_application_pk': self.good_on_application.id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GoodOnApplication.objects.filter(application=draft).count(), 0)
        self.assertEqual(self.good_on_application.good.status, GoodStatus.DRAFT)

    def test_remove_a_good_from_draft_success_when_good_is_verified(self):
        """
        Given a standard application with a good
        And the good's status is VERIFIED
        And there are no other applications with this good attached
        When I attempt to delete the good from the application
        Then the good_on_application is deleted
        And the good status is not changed
        """
        draft = self.create_standard_application(self.organisation)
        self.good_on_application.good.status = GoodStatus.VERIFIED
        self.good_on_application.good.save()

        url = reverse('applications:good_on_application',
                      kwargs={'good_on_application_pk': self.good_on_application.id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GoodOnApplication.objects.filter(application=draft).count(), 0)
        self.assertEqual(self.good_on_application.good.status, GoodStatus.VERIFIED)

    def test_remove_a_good_from_application_success_when_good_is_on_multiple_applications(self):
        """
        Given a standard application with a good
        And the good's status is VERIFIED
        And there are no other applications with this good attached
        When I attempt to delete the good from the application
        Then the good_on_application is deleted
        And the good status is not changed
        """
        application1 = self.create_standard_application(self.organisation)
        self.submit_application(application1)
        good_on_application1 = GoodOnApplication.objects.get(application=application1)

        application2 = self.create_standard_application(self.organisation)
        GoodOnApplication.objects.get(application=application2).delete()

        good_on_application2 = GoodOnApplication(good=good_on_application1.good,
                                                 application=application2,
                                                 quantity=10,
                                                 unit=Units.NAR,
                                                 value=500)
        good_on_application2.save()

        url = reverse('applications:good_on_application',
                      kwargs={'good_on_application_pk': good_on_application1.id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GoodOnApplication.objects.filter(application=application1).count(), 0)
        self.assertEqual(GoodOnApplication.objects.filter(application=application2).count(), 1)
        self.assertEqual(Good.objects.get(pk=good_on_application2.good.pk).status, GoodStatus.SUBMITTED)

    def test_remove_a_good_that_does_not_exist_from_draft(self):
        """
        Given a standard application with a good
        When I attempt to delete a good that doesn't exist
        Then the delete operation returns a not found response
        And no goods are deleted
        """
        draft = self.create_standard_application(self.organisation)

        url = reverse('applications:good_on_application',
                      kwargs={'good_on_application_pk': "7070dc05-0afa-482c-b4f7-ae0a8943e53c"})  # Imaginary UUID

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(GoodOnApplication.objects.filter(application=draft).count(), 1)

    def test_remove_a_good_from_draft_as_gov_user_failure(self):
        draft = self.create_standard_application(self.organisation)

        url = reverse('applications:good_on_application',
                      kwargs={'good_on_application_pk': self.good_on_application.id})

        response = self.client.delete(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(GoodOnApplication.objects.filter(application=draft).count(), 1)

    def test_remove_goods_from_application_not_in_users_organisation_failure(self):
        self.create_standard_application(self.organisation)
        url = reverse('applications:good_on_application',
                      kwargs={'good_on_application_pk': self.good_on_application.id})

        other_organisation, _ = self.create_organisation_with_exporter_user()
        permission_denied_user = UserOrganisationRelationship.objects.get(organisation=other_organisation).user
        permission_denied_user_headers = {
            'HTTP_EXPORTER_USER_TOKEN': user_to_token(permission_denied_user),
            'HTTP_ORGANISATION_ID': other_organisation.id
        }

        response = self.client.delete(url, **permission_denied_user_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @parameterized.expand(get_case_statuses(read_only=False))
    def test_delete_good_from_application_in_an_editable_status_success(self, editable_status):
        application = self.create_standard_application(self.organisation)
        application.status = get_case_status_by_status(editable_status)
        application.save()
        url = reverse('applications:good_on_application',
                        kwargs={'good_on_application_pk': self.good_on_application.id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GoodOnApplication.objects.filter(application=application).count(), 0)

    @parameterized.expand(get_case_statuses(read_only=True))
    def test_delete_good_from_application_in_read_only_status_failure(self, read_only_status):
        application = self.create_standard_application(self.organisation)
        application.status = get_case_status_by_status(read_only_status)
        application.save()
        url = reverse('applications:good_on_application',
                        kwargs={'good_on_application_pk': self.good_on_application.id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(GoodOnApplication.objects.filter(application=application).count(), 1)
