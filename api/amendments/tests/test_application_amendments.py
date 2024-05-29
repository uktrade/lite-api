from rest_framework import status
from rest_framework.reverse import reverse

from api.applications.models import StandardApplication
from api.applications.tests.factories import StandardApplicationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class CreateApplicationCopyTests(DataTestClient):

    def test_create_copy_of_application_success(self):
        application = StandardApplicationFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        )
        url = reverse("amendments:create_application_copy", kwargs={"case_pk": str(application.id)})
        response = self.client.post(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
