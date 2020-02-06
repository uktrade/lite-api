from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy

from applications.enums import (
    ApplicationType,
    ApplicationExportType,
    ApplicationExportLicenceOfficialType,
)
from applications.models import (
    StandardApplication,
    OpenApplication,
    HmrcQuery,
    BaseApplication,
    ExhibitionClearanceApplication,
    GoodOnApplication,
)
from goodstype.models import GoodsType
from lite_content.lite_api import strings
from parties.models import UltimateEndUser, ThirdParty
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class CopyTests(DataTestClient):

    # standard application
    def test_copy_draft_standard_application_successful(self):
        """
        Ensure we can copy a standard application that is a draft
        """
        self.original_application = self.create_standard_application(self.organisation)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application", "have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = StandardApplication.objects.get(id=self.response_data)

        self.standard_application_test()

    def test_copy_submitted_standard_application_successful(self):
        """
        Ensure we can copy a standard application that has been submitted (ongoing or not)
        """
        self.original_application = self.create_standard_application_case(self.organisation)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application", "have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = StandardApplication.objects.get(id=self.response_data)

        self.standard_application_test()

    def test_copy_draft_open_application_successful(self):
        """
        Ensure we can copy an open application that is a draft
        """
        self.original_application = self.create_open_application(self.organisation)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application", "have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = OpenApplication.objects.get(id=self.response_data)

        self.open_application_test()

    def test_copy_submitted_open_application_successful(self):
        """
        Ensure we can copy an open application that is submitted (ongoing or otherwise)
        """
        self.original_application = self.create_open_application(self.organisation)
        self.submit_application(self.original_application)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application", "have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = OpenApplication.objects.get(id=self.response_data)

        self.open_application_test()

    def test_copy_draft_exhibition_application_successful(self):
        """
        Ensure we can copy an exhibition application that is a draft
        """
        application = self.create_exhibition_clearance_application(self.organisation)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application"}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)

        self.exhibition_application_test()

    def test_copy_submitted_exhibition_application_successful(self):
        """
        Ensure we can copy an exhibition application that is submitted (ongoing or otherwise)
        """
        application = self.create_exhibition_clearance_application(self.organisation)
        self.submit_application(application)

        url = reverse_lazy("applications:copy", kwargs={"pk": application.id})

        data = {"name": "New application"}

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response_data, application.id)

        self.exhibition_application_test()

    def test_copy_draft_hmrc_enquiry_successful(self):
        """
        Ensure we can copy an hmrc enquiry that is a draft
        """
        self.original_application = self.create_hmrc_query(self.organisation)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application", "have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = HmrcQuery.objects.get(id=self.response_data)

        # self.hmrc_enquiry_test()

    def test_copy_submitted_hmrc_enquiry_successful(self):
        """
        Ensure we can copy an hmrc enquiry that is submitted ongoing or otherwise
        """
        self.original_application = self.create_hmrc_query(self.organisation)
        self.submit_application(self.original_application)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application", "have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = HmrcQuery.objects.get(id=self.response_data)

        # self.hmrc_enquiry_test()

    def standard_application_test(self):
        self.reset_data_test()

        self.good_on_application_test()

        self.end_user_test()
        self.consignee_test()
        self.ultimate_end_user_test()
        self.third_party_test()

        self.case_data_test()

    def open_application_test(self):
        self.reset_data_test()

        self.goodstype_test()  # update with goodtype

        self.country_on_application_test()

        self.case_data_test()

    def reset_data_test(self):
        self.assertEqual(self.copied_application.status, get_case_status_by_status(CaseStatusEnum.DRAFT))
        self.assertGreater(self.copied_application.created_at, self.original_application.created_at)

    def good_on_application_test(self):
        new_goods_on_app = self.copied_application.goods.all()
        original_goods_on_app = self.original_application.goods.all()
        for good_on_app in new_goods_on_app:
            self.assertNotIn(good_on_app, original_goods_on_app)
            original_good_on_app = GoodOnApplication.objects.get(
                application_id=self.original_application.id, good_id=good_on_app.good.id
            )

            self.assertEqual(good_on_app.good, original_good_on_app.good)
            self.assertEqual(good_on_app.value, original_good_on_app.value)
            self.assertEqual(good_on_app.quantity, original_good_on_app.quantity)
            self.assertEqual(good_on_app.unit, original_good_on_app.unit)
            self.assertGreater(good_on_app.created_at, original_good_on_app.created_at)

    def end_user_test(self):
        self.assertIsNotNone(self.copied_application.end_user)
        self.assertNotEqual(self.copied_application.end_user.id, self.original_application.end_user.id)
        self.assertGreater(self.copied_application.end_user.created_at, self.original_application.end_user.created_at)
        self.assertEqual(self.copied_application.end_user.name, self.original_application.end_user.name)
        self.assertEqual(self.copied_application.end_user.address, self.original_application.end_user.address)
        self.assertEqual(self.copied_application.end_user.country, self.original_application.end_user.country)
        self.assertEqual(self.copied_application.end_user.type, self.original_application.end_user.type)
        self.assertEqual(self.copied_application.end_user.sub_type, self.original_application.end_user.sub_type)

    def consignee_test(self):
        self.assertIsNotNone(self.copied_application.consignee)
        self.assertNotEqual(self.copied_application.consignee.id, self.original_application.consignee.id)
        self.assertGreater(self.copied_application.consignee.created_at, self.original_application.consignee.created_at)
        self.assertEqual(self.copied_application.consignee.name, self.original_application.consignee.name)
        self.assertEqual(self.copied_application.consignee.address, self.original_application.consignee.address)
        self.assertEqual(self.copied_application.consignee.country, self.original_application.consignee.country)
        self.assertEqual(self.copied_application.consignee.type, self.original_application.consignee.type)
        self.assertEqual(self.copied_application.consignee.sub_type, self.original_application.consignee.sub_type)

    def ultimate_end_user_test(self):
        self.assertIsNotNone(self.copied_application.ultimate_end_users)
        ultimate_end_users = self.copied_application.ultimate_end_users.all()
        original_ultimate_end_users = self.original_application.ultimate_end_users.all()
        for ueu in ultimate_end_users:
            self.assertNotIn(ueu, original_ultimate_end_users)
            original_ueu = UltimateEndUser.objects.get(id=ueu.copy_of_id, application_id=self.original_application.id)

            self.assertNotEqual(ueu.id, original_ueu.id)
            self.assertGreater(ueu.created_at, original_ueu.created_at)
            self.assertEqual(ueu.name, original_ueu.name)
            self.assertEqual(ueu.address, original_ueu.address)
            self.assertEqual(ueu.country, original_ueu.country)
            self.assertEqual(ueu.type, original_ueu.type)
            self.assertEqual(ueu.sub_type, original_ueu.sub_type)

    def third_party_test(self):
        self.assertIsNotNone(self.copied_application.third_parties)
        third_parties = self.copied_application.ultimate_end_users.all()
        original_third_parties = self.original_application.ultimate_end_users.all()
        for third_party in third_parties:
            self.assertNotIn(third_party, original_third_parties)
            original_third_party = ThirdParty.objects.get(
                id=third_party.copy_of_id, application_id=self.original_application.id
            )

            self.assertNotEqual(third_party.id, original_third_party.id)
            self.assertGreater(third_party.created_at, original_third_party.created_at)
            self.assertEqual(third_party.name, original_third_party.name)
            self.assertEqual(third_party.address, original_third_party.address)
            self.assertEqual(third_party.country, original_third_party.country)
            self.assertEqual(third_party.type, original_third_party.type)
            self.assertEqual(third_party.sub_type, original_third_party.sub_type)

    def case_data_test(self):
        self.assertEqual(list(self.copied_application.case_ecju_query.all()), [])
        self.assertEqual(list(self.copied_application.case_note.all()), [])
        self.assertEqual(list(self.copied_application.goodcountrydecision_set.all()), [])
        self.assertEqual(list(self.copied_application.advice_set.all()), [])
        self.assertEqual(list(self.copied_application.applicationdocument_set.all()), [])
        self.assertEqual(list(self.copied_application.casedocument_set.all()), [])

    def country_on_application_test(self):
        self.assertIsNotNone(self.copied_application.application_countries)

    def goodstype_test(self):
        goodstype_objects = GoodsType.objects.filter(application_id=self.copied_application.id)
        self.assertIsNotNone(goodstype_objects)
