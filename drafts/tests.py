import json

from django.urls import path, include
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from applications.models import Application
from drafts.models import Draft
from organisations.models import Organisation
from users.models import User


class DraftTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.draft_test_helper = DraftTestHelpers(name='name')
        self.headers = {'HTTP_USER_ID': str(self.draft_test_helper.user.id)}

    # Creation

    def test_create_draft(self):
        """
            Ensure we can create a new draft object.
        """
        url = reverse('drafts:drafts')
        data = {'name': 'test'}
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Draft.objects.count(), 1)
        self.assertEqual(Draft.objects.get().name, 'test')

    def test_create_draft_no_user_id(self):
        """
            Ensure we cannot create a draft without a name.
        """
        url = reverse('drafts:drafts')
        response = self.client.post(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Application.objects.count(), 0)

    # Editing

    def test_edit_draft(self):
        """
            Ensure we can edit a draft object.
        """
        draft = Draft(name='test',
                      organisation=self.draft_test_helper.organisation)
        draft.save()

        url = reverse('drafts:draft', kwargs={'pk': draft.id})
        data = {'destination': 'France'}
        response = self.client.put(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Draft.objects.count(), 1)
        self.assertEqual(Draft.objects.get().id, draft.id)
        self.assertEqual(Draft.objects.get().destination, 'France')

    # Viewing

    def test_view_drafts(self):
        """
            Ensure we can get a list of drafts.
        """

        complete_draft = Draft(user_id='12345',
                               control_code='ML2',
                               name='Test',
                               destination='Poland',
                               activity='Trade',
                               usage='Fun')
        complete_draft.save()

        url = '/drafts/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['drafts']), 1)

    # def test_view_drafts_not_applications(self):
    #     """
    #         Ensure that when a draft is submitted it does not get submitted as an application
    #     """
    #     draft_id = '90D6C724-0339-425A-99D2-9D2B8E864EC7'
    #     complete_draft = Draft(id=draft_id,
    #                            user_id='12345',
    #                            control_code='ML2',
    #                            name='Test',
    #                            destination='Poland',
    #                            activity='Trade',
    #                            usage='Fun')
    #     complete_draft.save()
    #
    #     url = '/applications/' + str(draft_id) + '/'
    #     response = self.client.get(url, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    #
    # def test_view_draft(self):
    #     """
    #         Ensure we can get a draft.
    #     """
    #     complete_draft = Draft(user_id='12345',
    #                            control_code='ML2',
    #                            name='Test',
    #                            destination='Poland',
    #                            activity='Trade',
    #                            usage='Fun')
    #
    #     complete_draft.save()
    #
    #     url = '/drafts/' + str(complete_draft.id) + '/'
    #     response = self.client.get(url, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #
    # def test_view_incorrect_draft(self):
    #     """
    #         Ensure we cannot get a draft if the id is incorrect.
    #     """
    #     complete_draft = Draft(user_id='12345',
    #                            control_code='ML2',
    #                            name='Test',
    #                            destination='Poland',
    #                            activity='Trade',
    #                            usage='Fun')
    #
    #     complete_draft.save()
    #     invalid_id = '90D6C724-0339-425A-99D2-9D2B8E864EC6'
    #
    #     url = '/drafts/' + str(invalid_id) + '/'
    #     response = self.client.get(url, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_only_sees_their_organisations_drafts_in_list(self):
        draft_test_helper_1 = DraftTestHelpers(name='organisation1')
        draft_test_helper_2 = DraftTestHelpers(name='organisation2')

        draft1 = Draft(name='test 1',
                       destination='Poland',
                       activity='fun',
                       usage='banter',
                       organisation=draft_test_helper_1.organisation)

        draft2 = Draft(name='test 2',
                       destination='France',
                       activity='work',
                       usage='play',
                       organisation=draft_test_helper_2.organisation)

        draft1.save()
        draft2.save()

        url = '/drafts/'
        response = self.client.get(url, **{'HTTP_USER_ID': str(draft_test_helper_1.user.id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["drafts"]), 1)


    # def test_user_cannot_see_details_of_another_organisations_draft(self):
    #     organisation1, user1 = DraftTestHelpers.create_organisation(name='organisation1')
    #     organisation2, user2 = DraftTestHelpers.create_organisation(name='organisation2')
    #
    #     draft1 = Draft(name='test 1',
    #                    destination='Poland',
    #                    activity='fun',
    #                    usage='banter',
    #                    organisation=organisation1)
    #
    #     draft2 = Draft(name='test 2',
    #                    destination='France',
    #                    activity='work',
    #                    usage='play',
    #                    organisation=organisation2)
    #
    #     draft1.save()
    #     draft2.save()
    #
    #     self.assertEqual(Draft.objects.count(), 2)
    #
    #     url = '/drafts/' + str(draft1.id)
    #     data = {'id': user1.id}
    #     # print(user1.id)
    #     # print(draft1.id)
    #     # print(url)
    #     response = self.client.get(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)


class DraftTestHelpers:
    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient()

    def __init__(self, name):
        # new_organisation = Organisation(name=name,
        #                                 eori_number='GB123456789000',
        #                                 sic_number='2765',
        #                                 vat_number='123456789',
        #                                 registration_number='987654321',
        #                                 address='London')
        #
        # new_organisation.save()
        #
        # new_user = User(email='trinity@'+name+'.com',
        #                 organisation=new_organisation)
        # new_user.set_password('password')
        # new_user.save()

        self.name = name
        self.eori_number = "GB123456789000"
        self.sic_number = "2765"
        self.vat_number = "123456789"
        self.registration_number = "987654321"
        self.address = "London"
        self.admin_user_email = "trinity@"+name+".com"

        url = reverse('organisations:organisations')
        data = {'name': self.name, 'eori_number': self.eori_number, 'sic_number': self.sic_number, 'vat_number': self.vat_number,
                'registration_number': self.registration_number, 'address': self.address, 'admin_user_email': self.admin_user_email}
        self.client.post(url, data, format='json')

        self.organisation = Organisation.objects.get(name=name)
        self.user = User.objects.filter(organisation=self.organisation)[0]




