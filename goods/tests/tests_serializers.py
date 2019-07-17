from goods.enums import GoodControlled
from goods.serializers import GoodSerializer
from test_helpers.clients import DataTestClient


class OrganisationTests(DataTestClient):

    def test_serializer_validation_with_empty(self):
        data = {'description': '', 'control_code': '', 'is_good_controlled': '', 'is_good_end_product': ''}
        serializer = GoodSerializer(data=data)
        serializer.is_valid()
        self.assertIsNotNone(serializer.errors['description'])
        self.assertIsNotNone(serializer.errors['is_good_controlled'])
        self.assertIsNotNone(serializer.errors['is_good_end_product'])

    def test_serializer_validation_with_controlled(self):
        data = {'description': '', 'control_code': '', 'is_good_controlled': GoodControlled.YES, 'is_good_end_product': ''}
        serializer = GoodSerializer(data=data)
        serializer.is_valid()

        self.assertIsNotNone(serializer.errors['description'])
        self.assertIsNotNone(serializer.errors['control_code'])
        self.assertIsNotNone(serializer.errors['is_good_end_product'])

    def test_serializer_validation_with_decontrolled(self):
        data = {'description': '', 'control_code': '', 'is_good_controlled': GoodControlled.NO, 'is_good_end_product': ''}
        serializer = GoodSerializer(data=data)
        serializer.is_valid()
        self.assertIsNotNone(serializer.errors['description'])
        self.assertNotIn('control_code', serializer.errors)
        self.assertIsNotNone(serializer.errors['is_good_end_product'])

    def test_serializer_validation_with_unsure(self):
        data = {'description': '', 'control_code': '', 'is_good_controlled': GoodControlled.UNSURE, 'is_good_end_product': ''}
        serializer = GoodSerializer(data=data)
        serializer.is_valid()
        self.assertIsNotNone(serializer.errors['description'])
        self.assertIsNotNone(serializer.errors['is_good_end_product'])
