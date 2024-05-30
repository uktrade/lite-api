from rest_framework import status
from rest_framework.reverse import reverse

from api.applications.models import GoodOnApplication, StandardApplication
from api.applications.tests.factories import (
    GoodOnApplicationFactory,
    PartyOnApplicationFactory,
    StandardApplicationFactory,
)
from api.goods.models import Good
from api.goods.tests.factories import FirearmFactory, GoodFactory
from api.parties.enums import PartyType
from api.parties.tests.factories import PartyFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class CreateApplicationCopyTests(DataTestClient):

    def test_create_copy_of_application_success(self):
        application = StandardApplicationFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        )
        goods_on_application = [
            GoodOnApplicationFactory(
                application=application,
                good=GoodFactory(organisation=self.organisation),
                firearm_details=FirearmFactory(),
            )
            for _ in range(2)
        ]
        PartyOnApplicationFactory(application=application, party=PartyFactory(type=PartyType.CONSIGNEE))
        PartyOnApplicationFactory(application=application, party=PartyFactory(type=PartyType.END_USER))

        url = reverse("amendments:create_application_copy", kwargs={"case_pk": str(application.id)})
        response = self.client.post(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = response.json()
        cloned_application = StandardApplication.objects.get(id=response["id"])
        self.assertNotEqual(cloned_application.id, application.id)
        self.assertEqual(cloned_application.copy_of.id, application.id)
        self.assertEqual(cloned_application.name, f"{application.name} copy")
        self.assertEqual(cloned_application.goods.count(), application.goods.count())
        self.assertEqual(cloned_application.parties.count(), application.parties.count())
