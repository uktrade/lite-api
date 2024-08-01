from decimal import Decimal
import urllib

from django.test import override_settings
from django.conf import settings
import requests_mock

from api.applications.tests.factories import StandardApplicationFactory, GoodOnApplicationFactory
from api.goods.tests.factories import GoodFactory
from api.staticdata.control_list_entries.helpers import get_control_list_entry
from api.licences.enums import LicenceStatus
from api.licences.service import get_case_licences
from api.licences.tests.factories import StandardLicenceFactory, GoodOnLicenceFactory
from test_helpers.clients import DataTestClient
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class GetCaseLicenceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory()
        self.licence = StandardLicenceFactory(
            case=self.application,
            status=LicenceStatus.REVOKED,
            duration=100,
            reference_code="reference",
        )
        self.good = GoodFactory(organisation=self.application.organisation, is_good_controlled=True)
        self.good_on_application = GoodOnApplicationFactory(
            application=self.application, good=self.good, quantity=100.0, value=Decimal("1000.00")
        )
        self.good_on_licence = GoodOnLicenceFactory(
            good=self.good_on_application,
            quantity=self.good_on_application.quantity,
            usage=20.0,
            value=20,
            licence=self.licence,
        )

    @override_settings(LITE_HMRC_INTEGRATION_URL="http://localhost:8000", LITE_HMRC_INTEGRATION_ENABLED=True)
    def test_hmrc_mail_status(self):
        url_params = urllib.parse.urlencode({"id": self.licence.reference_code})
        url = f"{settings.LITE_HMRC_INTEGRATION_URL}/mail/licence/?{url_params}"

        with requests_mock.Mocker() as m:
            m.register_uri("GET", url, json={"status": "reply_sent"})
            assert self.licence.hmrc_mail_status() == "reply_sent"

    def test_get_application_licences(self):
        data = get_case_licences(self.application)[0]
        self.assertEqual(data["id"], str(self.licence.id))
        self.assertEqual(data["reference_code"], self.licence.reference_code)
        self.assertEqual(data["status"], LicenceStatus.to_str(self.licence.status))
        self.assertEqual(data["goods"][0]["control_list_entries"][0]["rating"], "ML1a")
        self.assertEqual(data["goods"][0]["name"], self.good.name)
        self.assertEqual(data["goods"][0]["description"], self.good.description)
        self.assertEqual(data["goods"][0]["quantity"], self.good_on_licence.quantity)
        self.assertEqual(data["goods"][0]["usage"], self.good_on_licence.usage)

    def test_get_application_licences_application_level_control_list_entry(self):
        self.good_on_application.is_good_controlled = False
        self.good_on_application.save()
        self.good_on_application.control_list_entries.add(get_control_list_entry("ML1a"))
        self.good_on_application.control_list_entries.add(get_control_list_entry("ML13d1"))

        data = get_case_licences(self.application)[0]

        self.assertEqual(data["goods"][0]["is_good_controlled"], False)
        # ignore order of control list entries
        self.assertEqual(set([x["rating"] for x in data["goods"][0]["control_list_entries"]]), {"ML1a", "ML13d1"})

    def test_get_application_licences_case_status(self):
        self.licence.case.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        self.licence.case.save()

        data = get_case_licences(self.application)[0]

        assert data["case_status"] == CaseStatusEnum.FINALISED
