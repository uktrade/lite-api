from django.test import TestCase, Client
from rest_framework import status

# Create your tests here.

class OrganisationTests(TestCase):

    def test_create_organisation(self):
        organisation_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"
        new_organisation = Organisation(id=organisation_id,
                                        name="Big Scary Guns ltd",
                                        eori_number="GB123456789000",
                                        sic_number="2765")

        new_organisation.save()

        url = '/organisations/'
        data = {'id': organisation_id}
        respsonse = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organisation.objects.get(id=organisation_id).name, "Big Scary Guns ltd")
        self.assertEqual(Organisation.objects.get(id=organisation_id).eori_number, "GB123456789000")
        self.assertEqual(Organisation.objects.get(id=organisation_id).sic_number, "2765")