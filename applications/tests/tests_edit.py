from django.urls import reverse
from rest_framework import status

from applications.models import Application, LicenceType, ExportType
from test_helpers.clients import DataTestClient


class ApplicationsTests(DataTestClient):

    def test_update_status_of_an_application(self):
        application = Application(id='90d6c724-0339-425a-99d2-9d2b8e864ec7',
                                  name='Test',
                                  licence_type=LicenceType.open_licence,
                                  export_type=ExportType.permanent,
                                  reference_number_on_information_form='',
                                  destination='Poland',
                                  activity='Trade',
                                  usage='Trade')
        application.save()

        url = reverse('applications:application', kwargs={'pk': application.id})
        data = {'id': application.id, 'status': 'withdrawn'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Application.objects.get(pk=application.id).status.name, "withdrawn")
