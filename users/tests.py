from django.test import TestCase
from organisations.models import Organisation
from users.models import User


class UserTests(TestCase):

    def test_user_model(self):
        new_organisation = Organisation(name="Big Scary Guns ltd",
                                        eori_number="GB123456789000",
                                        sic_number="2765",
                                        vat_number="123456789",
                                        registration_number="987654321",
                                        address="London")

        new_user = User(email="trinity@bsg.com",
                        password="trinity@bsg.com",
                        organisation=new_organisation)

        new_organisation.save()
        new_user.save()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'trinity@bsg.com')
        self.assertEqual(User.objects.get().password, 'trinity@bsg.com')
        self.assertEqual(User.objects.get().organisation, new_organisation)
