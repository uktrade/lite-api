from django.urls import reverse
from rest_framework import status
from django.test import override_settings

from api.cases.enums import AdviceType, CaseTypeEnum, AdviceLevel
from api.cases.tests.factories import GoodCountryDecisionFactory, FinalAdviceFactory
from api.goodstype.tests.factories import GoodsTypeFactory
from api.licences.tests.factories import LicenceFactory
from api.staticdata.countries.models import Country
from test_helpers.clients import DataTestClient
from api.applications.tests.factories import GoodOnApplicationFactory, GoodFactory


class AdviceDocumentsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.licence = LicenceFactory(case=self.case)
        self.template = self.create_letter_template(name="Template", case_types=[CaseTypeEnum.SIEL.id])
        self.url = reverse("cases:final_advice_documents", kwargs={"pk": self.case.id})

    def test_get_final_advice_no_documents(self):
        self.create_advice(self.gov_user, self.case, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.create_advice(self.gov_user, self.case, "end_user", AdviceType.REFUSE, AdviceLevel.FINAL)

        expected_format = {
            AdviceType.APPROVE: {"value": AdviceType.get_text(AdviceType.APPROVE)},
            AdviceType.REFUSE: {"value": AdviceType.get_text(AdviceType.REFUSE)},
        }

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["documents"], expected_format)

    @override_settings(FEATURE_INFORM_LETTER_ENABLED=True)
    def test_get_final_advice_no_documents_inform_feature_on(self):
        self.create_advice(self.gov_user, self.case, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.create_advice(self.gov_user, self.case, "end_user", AdviceType.REFUSE, AdviceLevel.FINAL)

        expected_format = {
            AdviceType.APPROVE: {"value": AdviceType.get_text(AdviceType.APPROVE)},
            AdviceType.REFUSE: {"value": AdviceType.get_text(AdviceType.REFUSE)},
            AdviceType.INFORM: {"value": AdviceType.get_text(AdviceType.INFORM)},
        }

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["documents"], expected_format)

    def test_get_final_advice_with_document(self):
        self.create_advice(self.gov_user, self.case, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.create_advice(self.gov_user, self.case, "end_user", AdviceType.REFUSE, AdviceLevel.FINAL)

        document_one = self.create_generated_case_document(
            self.case, self.template, advice_type=AdviceType.APPROVE, licence=self.licence
        )
        document_two = self.create_generated_case_document(
            self.case, self.template, advice_type=AdviceType.REFUSE, licence=self.licence
        )

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["documents"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data[AdviceType.APPROVE]["value"], AdviceType.get_text(AdviceType.APPROVE))
        self.assertEqual(
            list(response_data[AdviceType.APPROVE]["document"].keys()), ["id", "advice_type", "user", "created_at"]
        )
        self.assertEqual(response_data[AdviceType.APPROVE]["document"]["id"], str(document_one.pk))

        self.assertEqual(response_data[AdviceType.REFUSE]["value"], AdviceType.get_text(AdviceType.REFUSE))
        self.assertEqual(
            list(response_data[AdviceType.REFUSE]["document"].keys()), ["id", "advice_type", "user", "created_at"]
        )
        self.assertEqual(response_data[AdviceType.REFUSE]["document"]["id"], str(document_two.pk))

    def test_get_final_advice_with_no_licence_required_document_no_controlled_goods(self):
        self.create_advice(self.gov_user, self.case, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.create_advice(self.gov_user, self.case, "end_user", AdviceType.NO_LICENCE_REQUIRED, AdviceLevel.FINAL)

        document_no_license = self.create_generated_case_document(
            self.case, self.template, advice_type=AdviceType.NO_LICENCE_REQUIRED, licence=self.licence
        )

        good = GoodFactory(
            organisation=self.organisation,
            is_good_controlled=False,
            control_list_entries=["ML21"],
        )

        GoodOnApplicationFactory(application=self.case, good=good, is_good_controlled=False)

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["documents"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNone(response_data.get(AdviceType.APPROVE))

        self.assertEqual(
            response_data[AdviceType.NO_LICENCE_REQUIRED]["value"], AdviceType.get_text(AdviceType.NO_LICENCE_REQUIRED)
        )
        self.assertEqual(
            list(response_data[AdviceType.NO_LICENCE_REQUIRED]["document"]),
            ["id", "advice_type", "user", "created_at"],
        )
        self.assertEqual(response_data[AdviceType.NO_LICENCE_REQUIRED]["document"]["id"], str(document_no_license.pk))

    def test_get_final_advice_with_no_licence_required_document_controlled_goods(self):
        self.create_advice(self.gov_user, self.case, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.create_advice(self.gov_user, self.case, "end_user", AdviceType.NO_LICENCE_REQUIRED, AdviceLevel.FINAL)

        good = GoodFactory(
            organisation=self.organisation,
            is_good_controlled=True,
            control_list_entries=["ML21"],
        )

        GoodOnApplicationFactory(application=self.case, good=good, is_good_controlled=True)

        document_one = self.create_generated_case_document(
            self.case, self.template, advice_type=AdviceType.APPROVE, licence=self.licence
        )
        document_two = self.create_generated_case_document(
            self.case, self.template, advice_type=AdviceType.NO_LICENCE_REQUIRED, licence=self.licence
        )

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["documents"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data[AdviceType.APPROVE]["value"], AdviceType.get_text(AdviceType.APPROVE))
        self.assertEqual(
            list(response_data[AdviceType.APPROVE]["document"]), ["id", "advice_type", "user", "created_at"]
        )
        self.assertEqual(response_data[AdviceType.APPROVE]["document"]["id"], str(document_one.pk))

        self.assertEqual(
            response_data[AdviceType.NO_LICENCE_REQUIRED]["value"], AdviceType.get_text(AdviceType.NO_LICENCE_REQUIRED)
        )
        self.assertEqual(
            list(response_data[AdviceType.NO_LICENCE_REQUIRED]["document"]),
            ["id", "advice_type", "user", "created_at"],
        )
        self.assertEqual(response_data[AdviceType.NO_LICENCE_REQUIRED]["document"]["id"], str(document_two.pk))

    def test_get_final_advice_with_document_proviso(self):
        # Proviso advice should match up with approve document
        self.create_advice(self.gov_user, self.case, "good", AdviceType.PROVISO, AdviceLevel.FINAL)
        document = self.create_generated_case_document(
            self.case, self.template, advice_type=AdviceType.APPROVE, licence=self.licence
        )

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["documents"][AdviceType.APPROVE]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["value"], AdviceType.get_text(AdviceType.APPROVE))
        self.assertEqual(response_data["document"]["id"], str(document.pk))


class OpenApplicationAdviceDocumentsTests(DataTestClient):
    def test_get_final_advice_documents_refuse_good_on_country(self):
        case = self.create_open_application_case(self.organisation)
        url = reverse("cases:final_advice_documents", kwargs={"pk": case.id})
        country = Country.objects.first()
        goods_type = GoodsTypeFactory(application=case)
        goods_type.countries.set([country])
        FinalAdviceFactory(
            user=self.gov_user,
            team=self.team,
            case=case,
            goods_type=goods_type,
            type=AdviceType.APPROVE,
        )
        GoodCountryDecisionFactory(case=case, country=country, approve=False)

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["documents"]

        # GoodCountryDecision overrides the approve final advice with a rejection
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data, {"refuse": {"value": "Refuse"}})
