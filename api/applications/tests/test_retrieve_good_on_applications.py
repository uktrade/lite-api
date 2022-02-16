from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized
from rest_framework import status

from api.applications.libraries.case_status_helpers import get_case_statuses
from api.applications.models import GoodOnApplication
from api.flags.enums import SystemFlags
from api.goods.enums import GoodStatus
from api.goods.models import Good, FirearmGoodDetails
from api.users.models import UserOrganisationRelationship
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.units.enums import Units
from test_helpers.clients import DataTestClient
from api.users.libraries.user_to_token import user_to_token


class RetrieveGoodsTests(DataTestClient):
    def test_retrieve_a_good_on_application(self):
        draft = self.create_draft_standard_application(self.organisation)
        self.good_on_application.good.status = GoodStatus.VERIFIED
        self.good_on_application.good.save()

        url = reverse(
            "applications:good_on_application",
            kwargs={"obj_pk": self.good_on_application.id},
        )

        for headers in [self.gov_headers, self.exporter_headers]:
            response = self.client.get(url, **headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue("audit_trail" in response.json())
