import json

from django.urls import path, include
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from applications.models import Application
from drafts.models import Draft
from goods.models import Good
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
        DraftTestHelpers.complete_draft(name='test 1', org=self.draft_test_helper.organisation).save()
        DraftTestHelpers.complete_draft(name='test 2', org=self.draft_test_helper.organisation).save()

        url = '/drafts/'
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['drafts']), 2)

    def test_view_drafts_not_applications(self):
        """
            Ensure that when a draft is submitted it does not get submitted as an application
        """
        draft = DraftTestHelpers.complete_draft(name='test', org=self.draft_test_helper.organisation)

        url = '/applications/' + str(draft.id) + '/'
        response = self.client.get(url, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_draft(self):
        """
            Ensure we can get a draft.
        """
        draft = DraftTestHelpers.complete_draft(name='test', org=self.draft_test_helper.organisation)

        url = '/drafts/' + str(draft.id) + '/'
        response = self.client.get(url, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_incorrect_draft(self):
        """
            Ensure we cannot get a draft if the id is incorrect.
        """
        DraftTestHelpers.complete_draft(name='test', org=self.draft_test_helper.organisation)
        invalid_id = '90D6C724-0339-425A-99D2-9D2B8E864EC6'

        url = '/drafts/' + str(invalid_id) + '/'
        response = self.client.put(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_only_sees_their_organisations_drafts_in_list(self):
        draft_test_helper_2 = DraftTestHelpers(name='organisation2')

        draft = DraftTestHelpers.complete_draft(name='test', org=self.draft_test_helper.organisation)
        DraftTestHelpers.complete_draft(name='test', org=draft_test_helper_2.organisation)

        url = '/drafts/'
        response = self.client.get(url, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Draft.objects.count(), 2)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["drafts"]), 1)
        self.assertEqual(response_data["drafts"][0]["organisation"], str(draft.organisation.id))

    def test_user_cannot_see_details_of_another_organisations_draft(self):
        draft_test_helper_2 = DraftTestHelpers(name='organisation2')
        draft = DraftTestHelpers.complete_draft(name='test', org=draft_test_helper_2.organisation)

        url = '/drafts/' + str(draft.id) + '/'

        response = self.client.get(url, **{'HTTP_USER_ID': str(self.draft_test_helper.user.id)})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_a_good_to_a_draft(self):
        org = self.draft_test_helper.organisation
        draft = DraftTestHelpers.complete_draft('Goods test', org)
        good = DraftTestHelpers.create_controlled_good('A good', org)

        data = {
            'draft': draft.id,
            'good': good.id,
            'quantity': 1200,
            'unit': 'discrete',
            'end_use_case': 'fun',
            'value': 50000
        }

        url = '/drafts/' + str(draft.id) + '/goods/' + str(good.id) + '/'
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = '/drafts/' + str(draft.id) + '/goods/'
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["goods"]), 1)
        self.assertEqual(response_data["goods"][0]["good"], str(good.id))
        self.assertEqual(response_data["goods"][0]["draft"], str(draft.id))

    def test_user_cannot_add_another_organisations_good_to_a_draft(self):
        draft_test_helper_2 = DraftTestHelpers(name='organisation2')
        good = DraftTestHelpers.create_controlled_good('test', draft_test_helper_2.organisation)
        draft = DraftTestHelpers.complete_draft('test', self.draft_test_helper.organisation)

        data = {
            'draft': draft.id,
            'good': good.id,
            'quantity': 1200,
            'unit': 'kg',
            'end_use_case': 'fun',
            'value': 50000
        }

        url = '/drafts/' + str(draft.id) + '/goods/' + str(good.id) + '/'
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = '/drafts/' + str(draft.id) + '/goods/'
        response = self.client.get(url, **self.headers)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["goods"]), 0)


class DraftTestHelpers:
    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient()

    def __init__(self, name):
        self.name = name
        self.eori_number = "GB123456789000"
        self.sic_number = "2765"
        self.vat_number = "123456789"
        self.registration_number = "987654321"
        self.address = "London"
        self.admin_user_email = "trinity@"+name+".com"

        url = reverse('organisations:organisations')
        data = {'name': self.name, 'eori_number': self.eori_number, 'sic_number': self.sic_number,
                'vat_number': self.vat_number, 'registration_number': self.registration_number,
                'address': self.address, 'admin_user_email': self.admin_user_email}
        self.client.post(url, data, format='json')

        self.organisation = Organisation.objects.get(name=name)
        self.user = User.objects.filter(organisation=self.organisation)[0]

    @staticmethod
    def complete_draft(name, org):
        draft = Draft(name=name,
                      destination='Poland',
                      activity='Trade',
                      usage='Fun',
                      organisation=org)
        draft.save()
        return draft

    @staticmethod
    def create_controlled_good(description, org):
        good = Good(description=description,
                    is_good_controlled=True,
                    control_code='ML1',
                    is_good_end_product=True,
                    part_number='123456',
                    organisation=org)
        good.save()
        return good
