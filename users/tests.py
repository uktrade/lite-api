from django.test import TestCase
from organisations.models import Organisation
from users.models import User


class TestHelper:
    @staticmethod
    def create_user_and_organisation():
        new_organisation = Organisation(name='Banana Stand ltd',
                                        eori_number='GB123456789000',
                                        sic_number='2765',
                                        vat_number='123456789',
                                        registration_number='987654321',
                                        address='London')

        new_user = User(email='trinity@bsg.com',
                        organisation=new_organisation,
                        password='password')

        new_organisation.save()
        new_user.save()

        return new_user, new_organisation


class UserTests(TestCase):

    def test_user_model(self):
        new_user, new_organisation = TestHelper.create_user_and_organisation()

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'trinity@bsg.com')
        self.assertEqual(User.objects.get().password, 'password')
        self.assertEqual(User.objects.get().organisation, new_organisation)
