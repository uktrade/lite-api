from rest_framework.test import APITestCase

from goodstype.serializers import GoodsTypeSerializer
from test_helpers.org_and_user_helper import OrgAndUserHelper


class OrganisationTests(APITestCase):

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_serializer_validation_with_empty(self):
        data = {'description': '', 'control_code': '', 'is_good_controlled': '', 'is_good_end_product': ''}
        serializer = GoodsTypeSerializer(data=data)
        serializer.is_valid()
        self.assertIsNotNone(serializer.errors['description'])
        self.assertIsNotNone(serializer.errors['is_good_controlled'])
        self.assertIsNotNone(serializer.errors['is_good_end_product'])

    def test_serializer_validation_with_controlled(self):
        data = {'description': '', 'control_code': '', 'is_good_controlled': 'True', 'is_good_end_product': ''}
        serializer = GoodsTypeSerializer(data=data)
        serializer.is_valid()
        self.assertIsNotNone(serializer.errors['description'])
        self.assertIsNotNone(serializer.errors['control_code'])
        self.assertIsNotNone(serializer.errors['is_good_end_product'])

    def test_serializer_validation_with_decontrolled(self):
        data = {'description': '', 'control_code': '', 'is_good_controlled': 'False', 'is_good_end_product': ''}
        serializer = GoodsTypeSerializer(data=data)
        serializer.is_valid()
        self.assertIsNotNone(serializer.errors['description'])
        self.assertNotIn('control_code', serializer.errors)
        self.assertIsNotNone(serializer.errors['is_good_end_product'])
