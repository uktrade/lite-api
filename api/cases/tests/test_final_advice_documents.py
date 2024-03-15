from django.urls import reverse
from rest_framework import status

from api.cases.enums import AdviceType, CaseTypeEnum
from api.cases.tests.factories import FinalAdviceFactory
from api.licences.tests.factories import StandardLicenceFactory
from test_helpers.clients import DataTestClient
from api.applications.tests.factories import GoodOnApplicationFactory, GoodFactory


class AdviceDocumentsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.good = self.case.goods.first().good
        self.end_user = self.case.end_user.party
        self.licence = StandardLicenceFactory(case=self.case)
        self.template = self.create_letter_template(name="Template", case_types=[CaseTypeEnum.SIEL.id])
        self.url = reverse("cases:final_advice_documents", kwargs={"pk": self.case.id})

    def test_get_final_advice_no_documents(self):
        FinalAdviceFactory(user=self.gov_user, case=self.case, type=AdviceType.APPROVE, good=self.good)
        FinalAdviceFactory(user=self.gov_user, case=self.case, type=AdviceType.REFUSE, end_user=self.end_user)
        expected_format = {
            AdviceType.APPROVE: {"value": AdviceType.get_text(AdviceType.APPROVE)},
            AdviceType.REFUSE: {"value": AdviceType.get_text(AdviceType.REFUSE)},
            AdviceType.INFORM: {"value": AdviceType.get_text(AdviceType.INFORM)},
        }

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["documents"], expected_format)

    def test_get_final_advice_with_document(self):
        FinalAdviceFactory(user=self.gov_user, case=self.case, type=AdviceType.APPROVE, good=self.good)
        FinalAdviceFactory(user=self.gov_user, case=self.case, type=AdviceType.REFUSE, end_user=self.end_user)

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
            list(response_data[AdviceType.APPROVE]["document"].keys()),
            ["id", "advice_type", "user", "created_at", "visible_to_exporter"],
        )
        self.assertEqual(response_data[AdviceType.APPROVE]["document"]["id"], str(document_one.pk))

        self.assertEqual(response_data[AdviceType.REFUSE]["value"], AdviceType.get_text(AdviceType.REFUSE))
        self.assertEqual(
            list(response_data[AdviceType.REFUSE]["document"].keys()),
            ["id", "advice_type", "user", "created_at", "visible_to_exporter"],
        )
        self.assertEqual(response_data[AdviceType.REFUSE]["document"]["id"], str(document_two.pk))

    def test_get_final_advice_with_no_licence_required_document_no_controlled_goods(self):
        FinalAdviceFactory(user=self.gov_user, case=self.case, type=AdviceType.APPROVE, good=self.good)
        FinalAdviceFactory(
            user=self.gov_user, case=self.case, type=AdviceType.NO_LICENCE_REQUIRED, end_user=self.end_user
        )

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
            ["id", "advice_type", "user", "created_at", "visible_to_exporter"],
        )
        self.assertEqual(response_data[AdviceType.NO_LICENCE_REQUIRED]["document"]["id"], str(document_no_license.pk))

    def test_get_final_advice_with_no_licence_required_document_controlled_goods(self):
        FinalAdviceFactory(user=self.gov_user, case=self.case, type=AdviceType.APPROVE, good=self.good)
        FinalAdviceFactory(
            user=self.gov_user, case=self.case, type=AdviceType.NO_LICENCE_REQUIRED, end_user=self.end_user
        )

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
            list(response_data[AdviceType.APPROVE]["document"]),
            ["id", "advice_type", "user", "created_at", "visible_to_exporter"],
        )
        self.assertEqual(response_data[AdviceType.APPROVE]["document"]["id"], str(document_one.pk))

        self.assertEqual(
            response_data[AdviceType.NO_LICENCE_REQUIRED]["value"], AdviceType.get_text(AdviceType.NO_LICENCE_REQUIRED)
        )
        self.assertEqual(
            list(response_data[AdviceType.NO_LICENCE_REQUIRED]["document"]),
            ["id", "advice_type", "user", "created_at", "visible_to_exporter"],
        )
        self.assertEqual(response_data[AdviceType.NO_LICENCE_REQUIRED]["document"]["id"], str(document_two.pk))

    def test_get_final_advice_with_document_proviso(self):
        # Proviso advice should match up with approve document
        FinalAdviceFactory(user=self.gov_user, case=self.case, type=AdviceType.PROVISO, good=self.good)
        document = self.create_generated_case_document(
            self.case, self.template, advice_type=AdviceType.APPROVE, licence=self.licence
        )

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["documents"][AdviceType.APPROVE]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["value"], AdviceType.get_text(AdviceType.APPROVE))
        self.assertEqual(response_data["document"]["id"], str(document.pk))
