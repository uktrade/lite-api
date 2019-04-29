from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from rest_framework.reverse import reverse
from django.urls import path, include

from goods.models import Good
from test_helpers.org_and_user_helper import OrgAndUserHelper


class OrganisationTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('goods/', include('goods.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_view_good_details(self):
        good = Good(description='thing',
                    is_good_controlled=False,
                    is_good_end_product=True,
                    organisation=self.test_helper.organisation)
        good.save()

        url = reverse('goods:good', kwargs={'pk': good.id})
        response = self.client.get(url, **{'HTTP_USER_ID': str(self.test_helper.user.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_fail_view_other_organisations_goods_details(self):
        test_helper_2 = OrgAndUserHelper(name='organisation2')

        good = Good(description='thing',
                    is_good_controlled=False,
                    is_good_end_product=True,
                    organisation=self.test_helper.organisation)
        good.save()

        url = reverse('goods:good', kwargs={'pk': good.id})
        response = self.client.get(url, **{'HTTP_USER_ID': str(test_helper_2.user.id)})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)