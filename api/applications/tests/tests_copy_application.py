from uuid import uuid4

from rest_framework import status
from rest_framework.reverse import reverse_lazy

from api.applications.enums import ApplicationExportLicenceOfficialType, ApplicationExportType
from api.applications.models import (
    StandardApplication,
    OpenApplication,
    HmrcQuery,
    GoodOnApplication,
    CountryOnApplication,
    SiteOnApplication,
    ExhibitionClearanceApplication,
    GiftingClearanceApplication,
    F680ClearanceApplication,
)
from cases.enums import CaseTypeEnum, CaseTypeSubTypeEnum
from api.goodstype.models import GoodsType
from api.parties.models import Party, PartyDocument
from api.static.statuses.enums import CaseStatusEnum
from api.static.statuses.libraries.get_case_status import get_case_status_by_status
from api.static.trade_control.enums import TradeControlProductCategory, TradeControlActivity
from test_helpers.clients import DataTestClient


class CopyApplicationSuccessTests(DataTestClient):
    # standard application
    def test_copy_draft_standard_application_successful(self):
        """
        Ensure we can copy a standard application that is a draft
        """
        self.original_application = self.create_draft_standard_application(self.organisation)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {
            "name": "New application",
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "54321-12",
        }

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = StandardApplication.objects.get(id=self.response_data)

        self._validate_standard_application()

    def test_copy_draft_standard_trade_control_application_successful(self):
        """
        Ensure we can copy a standard trade control application that is a draft
        """
        self.original_application = self.create_draft_standard_application(self.organisation)
        self.original_application.trade_control_activity = TradeControlActivity.OTHER
        self.original_application.trade_control_activity_other = "other activity"
        self.original_application.trade_control_product_categories = [
            key for key, _ in TradeControlProductCategory.choices
        ]
        self.original_application.save()

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {
            "name": "New application",
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "54321-12",
        }

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = StandardApplication.objects.get(id=self.response_data)

        self._validate_standard_application()

    def test_copy_draft_standard_temporary_application_successful(self):
        """
        Ensure we can copy a standard temporary application that is a draft
        """
        self.original_application = self.create_draft_standard_application(self.organisation)
        self.original_application.export_type = ApplicationExportType.TEMPORARY
        self.original_application.temp_export_details = "temporary export details"
        self.original_application.is_temp_direct_control = True
        self.original_application.proposed_return_date = "2025-05-11"
        self.submit_application(self.original_application)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {
            "name": "New application",
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "54321-12",
        }

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = StandardApplication.objects.get(id=self.response_data)

        self._validate_standard_application()

    def test_copy_submitted_standard_application_successful(self):
        """
        Ensure we can copy a standard application that has been submitted (ongoing or not)
        """
        self.original_application = self.create_standard_application_case(self.organisation)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {
            "name": "New application",
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "54321-12",
        }

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = StandardApplication.objects.get(id=self.response_data)

        self._validate_standard_application()

    def test_copy_submitted_standard_temporary_application_successful(self):
        """
        Ensure we can copy a standard temporary application that has been submitted (ongoing or not)
        """
        self.original_application = self.create_draft_standard_application(self.organisation)
        self.original_application.export_type = ApplicationExportType.TEMPORARY
        self.original_application.temp_export_details = "temporary export details"
        self.original_application.is_temp_direct_control = True
        self.original_application.proposed_return_date = "2025-05-11"

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {
            "name": "New application",
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "54321-12",
        }

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = StandardApplication.objects.get(id=self.response_data)

        self._validate_standard_application()

    def test_copy_draft_open_application_successful(self):
        """
        Ensure we can copy an open application that is a draft
        """
        self.original_application = self.create_draft_open_application(self.organisation)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = OpenApplication.objects.get(id=self.response_data)

        self._validate_open_application()

    def test_copy_draft_open_trade_control_application_successful(self):
        """
        Ensure we can copy an open application that is a draft
        """
        self.original_application = self.create_draft_open_application(
            self.organisation, case_type_id=CaseTypeEnum.OICL.id
        )
        self.original_application.trade_control_activity = TradeControlActivity.OTHER
        self.original_application.trade_control_activity_other = "other activity"
        self.original_application.trade_control_product_categories = [
            key for key, _ in TradeControlProductCategory.choices
        ]
        self.original_application.save()

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = OpenApplication.objects.get(id=self.response_data)

        self._validate_open_application()

    def test_copy_draft_open_temporary_application_successful(self):
        """
        Ensure we can copy an open temporary application that is a draft
        """
        self.original_application = self.create_draft_open_application(self.organisation)
        self.original_application.export_type = ApplicationExportType.TEMPORARY
        self.original_application.temp_export_details = "temporary export details"
        self.original_application.is_temp_direct_control = True
        self.original_application.proposed_return_date = "2025-05-11"

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = OpenApplication.objects.get(id=self.response_data)

        self._validate_open_application()

    def test_copy_submitted_open_temporary_application_successful(self):
        """
        Ensure we can copy an open temporary application that is submitted (ongoing or otherwise)
        """
        self.original_application = self.create_draft_open_application(self.organisation)
        self.original_application.export_type = ApplicationExportType.TEMPORARY
        self.original_application.temp_export_details = "temporary export details"
        self.original_application.is_temp_direct_control = True
        self.original_application.proposed_return_date = "2025-05-11"
        coa = CountryOnApplication.objects.get(application=self.original_application, country_id="FR")
        coa.contract_types = ["navy", "army"]
        coa.save()

        self.submit_application(self.original_application)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = OpenApplication.objects.get(id=self.response_data)

        self._validate_open_application()

    def test_copy_submitted_open_application_successful(self):
        """
        Ensure we can copy an open application that is submitted (ongoing or otherwise)
        """
        self.original_application = self.create_draft_open_application(self.organisation)
        self.submit_application(self.original_application)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = OpenApplication.objects.get(id=self.response_data)

        self._validate_open_application()

    def test_copy_draft_exhibition_application_successful(self):
        """
        Ensure we can copy an exhibition application that is a draft
        """
        self.original_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = ExhibitionClearanceApplication.objects.get(id=self.response_data)

        self._validate_exhibition_application()

    def test_copy_submitted_exhibition_application_successful(self):
        """
        Ensure we can copy an exhibition application that is submitted (ongoing or otherwise)
        """
        self.original_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.submit_application(self.original_application)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = ExhibitionClearanceApplication.objects.get(id=self.response_data)

        self._validate_exhibition_application()

    def test_copy_draft_gifting_application_successful(self):
        """
        Ensure we can copy an exhibition application that is a draft
        """
        self.original_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.GIFTING)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = GiftingClearanceApplication.objects.get(id=self.response_data)

        self._validate_gifting_application()

    def test_copy_submitted_gifting_application_successful(self):
        """
        Ensure we can copy an exhibition application that is submitted (ongoing or otherwise)
        """
        self.original_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.GIFTING)
        self.submit_application(self.original_application)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = GiftingClearanceApplication.objects.get(id=self.response_data)

        self._validate_gifting_application()

    def test_copy_draft_F680_application_successful(self):
        """
        Ensure we can copy an f680 application that is a draft
        """
        self.original_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = F680ClearanceApplication.objects.get(id=self.response_data)

        self._validate_F680_application()

    def test_copy_submitted_F680_application_successful(self):
        """
        Ensure we can copy an f680 application that is submitted (ongoing or otherwise)
        """
        self.original_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        self.submit_application(self.original_application)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = F680ClearanceApplication.objects.get(id=self.response_data)

        self._validate_F680_application()

    def test_copy_draft_hmrc_enquiry_successful(self):
        """
        Ensure we can copy an hmrc enquiry that is a draft
        """
        self.original_application = self.create_hmrc_query(self.organisation)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = HmrcQuery.objects.get(id=self.response_data)

        self._validate_hmrc_enquiry()

    def test_copy_submitted_hmrc_enquiry_successful(self):
        """
        Ensure we can copy an hmrc enquiry that is submitted ongoing or otherwise
        """
        self.original_application = self.create_hmrc_query(self.organisation)
        self.submit_application(self.original_application)

        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})

        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.response_data = self.response.json()["data"]

        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(self.response_data, self.original_application.id)

        self.copied_application = HmrcQuery.objects.get(id=self.response_data)

        self._validate_hmrc_enquiry()

    def _validate_standard_application(self):
        self._validate_reset_data()
        self._validate_end_use_details()
        self._validate_good_on_application()
        self._validate_end_user()
        self._validate_consignee()
        self._validate_ultimate_end_user()
        self._validate_third_party()
        self._validate_case_data()
        self._validate_route_of_goods()
        self._validate_temporary_export_details()
        self._validate_trade_control_details()

    def _validate_open_application(self):
        self._validate_reset_data()
        self._validate_end_use_details()
        self._validate_goodstype()
        self._validate_site_on_application()
        self._validate_country_on_application()
        self._validate_case_data()
        self._validate_route_of_goods()
        self._validate_temporary_export_details()
        self._validate_trade_control_details()

    def _validate_trade_control_details(self):
        if self.original_application.case_type.id in [CaseTypeEnum.SICL.id, CaseTypeEnum.OICL.id]:
            self.assertEqual(
                self.original_application.trade_control_activity, self.copied_application.trade_control_activity
            )
            self.assertEqual(
                self.original_application.trade_control_product_categories,
                self.copied_application.trade_control_product_categories,
            )

    def _validate_exhibition_application(self):
        self._validate_reset_data()

        self.assertEqual(self.original_application.title, self.copied_application.title)
        self.assertEqual(self.original_application.first_exhibition_date, self.copied_application.first_exhibition_date)
        self.assertEqual(self.original_application.required_by_date, self.copied_application.required_by_date)
        self.assertEqual(self.original_application.reason_for_clearance, self.copied_application.reason_for_clearance)

        self._validate_good_on_application()

        self._validate_case_data()

    def _validate_gifting_application(self):
        self._validate_reset_data()

        self._validate_good_on_application()

        self._validate_end_user()
        self._validate_third_party()

        self._validate_case_data()

    def _validate_F680_application(self):
        self._validate_reset_data()

        self._validate_f680_clearance_types()

        self._validate_end_use_details(self.copied_application.case_type.sub_type)

        self._validate_good_on_application()

        self._validate_end_user()
        self._validate_third_party()

        self._validate_case_data()

    def _validate_hmrc_enquiry(self):
        self._validate_reset_data()
        self.assertEqual(self.original_application.reasoning, self.copied_application.reasoning)
        self.assertEqual(self.original_application.have_goods_departed, self.copied_application.have_goods_departed)

        self._validate_goodstype()

        self._validate_end_user()
        self._validate_consignee()
        self._validate_ultimate_end_user()
        self._validate_third_party()

        self._validate_case_data()

    def _validate_reset_data(self):
        self.assertNotEqual(self.copied_application.id, self.original_application.id)
        self.assertEqual(self.copied_application.copy_of.id, self.original_application.id)
        self.assertEqual(self.copied_application.status, get_case_status_by_status(CaseStatusEnum.DRAFT))
        self.assertGreater(self.copied_application.created_at, self.original_application.created_at)
        self.assertGreater(self.copied_application.updated_at, self.original_application.updated_at)

    def _validate_end_use_details(self, application_type=None):
        if application_type == CaseTypeSubTypeEnum.F680:
            self.assertIsNone(self.copied_application.intended_end_use)
        elif application_type in [CaseTypeSubTypeEnum.STANDARD, CaseTypeSubTypeEnum.OPEN]:
            self.assertIsNone(self.copied_application.intended_end_use)
            self.assertIsNone(self.copied_application.is_informed_wmd)
            self.assertIsNone(self.copied_application.is_suspected_wmd)
            self.assertIsNone(self.copied_application.is_military_end_use_controls)
            if application_type == CaseTypeSubTypeEnum.STANDARD:
                self.assertIsNone(self.copied_application.is_eu_military)
                self.assertIsNone(self.copied_application.is_compliant_limitations_eu)
                self.assertIsNone(self.copied_application.compliant_limitations_eu_ref)

    def _validate_route_of_goods(self):
        self.assertIsNone(self.copied_application.is_shipped_waybill_or_lading)
        self.assertIsNone(self.copied_application.non_waybill_or_lading_route_details)

    def _validate_temporary_export_details(self, export_type=None):
        if export_type == ApplicationExportType.TEMPORARY:
            self.assertIsNone(self.copied_application.temp_export_details)
            self.assertIsNone(self.copied_application.is_temp_direct_control)
            self.assertIsNone(self.copied_application.temp_direct_control_details)
            self.assertIsNone(self.copied_application.proposed_return_date)

    def _validate_good_on_application(self):
        new_goods_on_app = self.copied_application.goods.all()
        original_goods_on_app = self.original_application.goods.all()
        for good_on_app in original_goods_on_app:
            self.assertNotIn(good_on_app, new_goods_on_app)

            new_good_on_app = GoodOnApplication.objects.get(
                application_id=self.original_application.id, good_id=good_on_app.good.id
            )

            self.assertEqual(good_on_app.good, new_good_on_app.good)
            self.assertEqual(good_on_app.value, new_good_on_app.value)
            self.assertEqual(good_on_app.quantity, new_good_on_app.quantity)
            self.assertEqual(good_on_app.unit, new_good_on_app.unit)

        self.assertEqual(len(new_goods_on_app), len(original_goods_on_app))

    def _validate_f680_clearance_types(self):
        new_types_app = self.copied_application.types.all()
        original_types_on_app = self.original_application.types.all()
        for type in original_types_on_app:
            self.assertIn(type, new_types_app)

    def _validate_party_details(self, new_party, original_party):
        self.assertNotEqual(new_party.id, original_party.id)
        self.assertGreater(new_party.created_at, original_party.created_at)
        self.assertGreater(new_party.updated_at, original_party.updated_at)
        self.assertEqual(new_party.name, original_party.name)
        self.assertEqual(new_party.address, original_party.address)
        self.assertEqual(new_party.country, original_party.country)
        self.assertEqual(new_party.type, original_party.type)
        self.assertEqual(new_party.sub_type, original_party.sub_type)
        self.assertEqual(list(PartyDocument.objects.filter(party=new_party).all()), [])

    def _validate_end_user(self):
        self.assertIsNotNone(self.copied_application.end_user)
        self._validate_party_details(self.copied_application.end_user.party, self.original_application.end_user.party)

    def _validate_consignee(self):
        self.assertIsNotNone(self.copied_application.consignee)
        self._validate_party_details(self.copied_application.consignee.party, self.original_application.consignee.party)

    def _validate_ultimate_end_user(self):
        self.assertIsNotNone(self.copied_application.ultimate_end_users)
        ultimate_end_users = self.copied_application.ultimate_end_users.all()
        original_ultimate_end_users = self.original_application.ultimate_end_users.all()
        self.assertEqual(len(ultimate_end_users), len(original_ultimate_end_users))
        original_ultimate_end_users_id = list(self.original_application.ultimate_end_users.values("id"))
        for ueu in ultimate_end_users:
            self.assertNotIn(ueu, original_ultimate_end_users)
            original_ueu = Party.objects.get(id=ueu.copy_of_id, application_id=self.original_application.id)
            original_ultimate_end_users_id.remove(ueu.copy_of_id)
            self._validate_party_details(ueu, original_ueu)

        self.assertEqual(len(original_ultimate_end_users_id), 0)

    def _validate_third_party(self):
        self.assertIsNotNone(self.copied_application.third_parties)
        third_parties = self.copied_application.ultimate_end_users.all()
        original_third_parties = self.original_application.ultimate_end_users.all()
        self.assertEqual(len(third_parties), len(original_third_parties))
        original_third_parties_id = list(self.original_application.ultimate_end_users.values("id"))
        for third_party in third_parties:
            self.assertNotIn(third_party, original_third_parties)
            original_third_party = Party.objects.get(
                id=third_party.copy_of_id, application_id=self.original_application.id
            )
            original_third_parties_id.remove(third_party.copy_of_id)
            self._validate_party_details(third_party, original_third_party)

        self.assertEqual(len(original_third_parties_id), 0)

    def _validate_case_data(self):
        self.assertEqual(list(self.copied_application.case_ecju_query.all()), [])
        self.assertEqual(list(self.copied_application.case_notes.all()), [])
        self.assertEqual(list(self.copied_application.goodcountrydecision_set.all()), [])
        self.assertEqual(list(self.copied_application.get_case().advice.all()), [])
        self.assertEqual(list(self.copied_application.applicationdocument_set.all()), [])
        self.assertEqual(list(self.copied_application.casedocument_set.all()), [])

    def _validate_country_on_application(self):
        self.assertIsNotNone(self.copied_application.application_countries)
        new_countries = list(
            CountryOnApplication.objects.filter(application=self.copied_application).values("country").all()
        )
        for country in (
            CountryOnApplication.objects.filter(application=self.original_application).values("country").all()
        ):
            self.assertIn(country, new_countries)

    def _validate_site_on_application(self):
        self.assertIsNotNone(self.copied_application.application_sites)
        new_sites = list(SiteOnApplication.objects.filter(application=self.copied_application).values("site").all())
        old_sites = SiteOnApplication.objects.filter(application=self.original_application).values("site").all()
        self.assertEqual(len(new_sites), len(old_sites))
        for site in old_sites:
            self.assertIn(site, new_sites)

    def _validate_goodstype(self):
        new_goodstype_objects = GoodsType.objects.filter(application_id=self.copied_application.id)
        self.assertIsNotNone(new_goodstype_objects)

        for goodstype in new_goodstype_objects:
            # we seed multiple goodstype with the same data currently, so testing that there are the same amount of
            #  goodstype on both old and new application based on the current goodstype data.
            control_list_entries_ids = goodstype.control_list_entries.values_list("id", flat=True)
            old_goodsType = len(
                GoodsType.objects.filter(
                    description=goodstype.description,
                    is_good_controlled=goodstype.is_good_controlled,
                    control_list_entries__in=control_list_entries_ids,
                    is_good_incorporated=goodstype.is_good_incorporated,
                    application=self.original_application,
                ).all()
            )
            new_goodsType = len(
                GoodsType.objects.filter(
                    description=goodstype.description,
                    is_good_controlled=goodstype.is_good_controlled,
                    control_list_entries__in=control_list_entries_ids,
                    is_good_incorporated=goodstype.is_good_incorporated,
                    application=self.copied_application,
                    usage=0,
                ).all()
            )

            self.assertEqual(old_goodsType, new_goodsType)


class CopyApplicationFailTests(DataTestClient):
    def test_copy_bad_pk(self):
        self.url = reverse_lazy("applications:copy", kwargs={"pk": uuid4()})
        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(self.response.status_code, status.HTTP_404_NOT_FOUND)

    # standard
    def test_copy_standard_application_missing_data_informed(self):
        """
        Ensure we can copy a standard application that is a draft
        """
        self.original_application = self.create_draft_standard_application(self.organisation)
        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})
        self.data = {"name": "New application"}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(self.response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_copy_missing_data_name(self):
        """
        Ensure we can copy a standard application that is a draft
        """
        self.original_application = self.create_draft_standard_application(self.organisation)
        self.url = reverse_lazy("applications:copy", kwargs={"pk": self.original_application.id})
        self.data = {"have_you_been_informed": ApplicationExportLicenceOfficialType.YES}

        self.response = self.client.post(self.url, self.data, **self.exporter_headers)

        self.assertEqual(self.response.status_code, status.HTTP_400_BAD_REQUEST)
