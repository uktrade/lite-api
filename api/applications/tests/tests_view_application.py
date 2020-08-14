from uuid import UUID

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.applications.models import (
    GoodOnApplication,
    CountryOnApplication,
    SiteOnApplication,
)
from cases.enums import CaseTypeEnum
from api.goodstype.models import GoodsType
from api.organisations.tests.factories import SiteFactory
from static.statuses.enums import CaseStatusEnum
from static.trade_control.enums import TradeControlActivity, TradeControlProductCategory
from test_helpers.clients import DataTestClient
from api.users.libraries.get_user import get_user_organisation_relationship


class DraftTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("applications:applications") + "?submitted=false"

    def test_view_draft_standard_application_list_as_exporter_success(self):
        """
        Ensure we can get a list of drafts.
        """
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        standard_application = self.create_draft_standard_application(self.organisation)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["name"], standard_application.name)
        self.assertEqual(response_data[0]["case_type"]["sub_type"]["key"], standard_application.case_type.sub_type)
        self.assertIsNotNone(response_data[0]["updated_at"])
        self.assertEqual(response_data[0]["status"]["key"], CaseStatusEnum.DRAFT)

    def test_ensure_user_cannot_see_applications_they_dont_have_access_to(self):
        """
        Ensure that the exporter cannot see applications with sites that they don't have access to.
        """
        self.create_draft_standard_application(self.organisation)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)

    def test_ensure_user_cannot_see_applications_they_only_have_partial_access_to_(self):
        """
        Ensure that the exporter cannot see applications with sites that they don't have access to AND
        sites that they are assigned to.
        """
        relationship = get_user_organisation_relationship(self.exporter_user, self.organisation)
        relationship.sites.set([self.organisation.primary_site])
        site_2 = SiteFactory(organisation=self.organisation)
        application = self.create_draft_standard_application(self.organisation)
        SiteOnApplication(site=site_2, application=application).save()

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)

    def test_cant_view_draft_hmrc_query_list_as_exporter_success(self):
        self.create_hmrc_query(organisation=self.organisation)

        response = self.client.get(self.url, **self.exporter_headers)

        result_count = response.json()["count"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result_count, 0)

    def test_view_hmrc_query_list_as_hmrc_exporter_success(self):
        """
        Ensure we can get a list of HMRC queries.
        """
        hmrc_query = self.create_hmrc_query(organisation=self.organisation)

        response = self.client.get(self.url, **self.hmrc_exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["name"], hmrc_query.name)
        self.assertEqual(response_data[0]["case_type"]["sub_type"]["key"], hmrc_query.case_type.sub_type)
        self.assertIsNotNone(response_data[0]["updated_at"])
        self.assertEqual(response_data[0]["status"]["key"], CaseStatusEnum.DRAFT)

    def test_view_draft_standard_application_as_exporter_success(self):
        standard_application = self.create_draft_standard_application(self.organisation)

        url = reverse("applications:application", kwargs={"pk": standard_application.id})

        response = self.client.get(url, **self.exporter_headers)

        retrieved_application = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_application["id"], str(standard_application.id))
        self.assertEqual(retrieved_application["name"], standard_application.name)
        self.assertEqual(
            retrieved_application["case_type"]["reference"]["key"], standard_application.case_type.reference,
        )
        self.assertEqual(
            retrieved_application["export_type"]["key"], standard_application.export_type,
        )
        self.assertIsNotNone(retrieved_application["created_at"])
        self.assertIsNotNone(retrieved_application["updated_at"])
        self.assertIsNone(retrieved_application["submitted_at"])
        self.assertEqual(retrieved_application["status"]["key"], CaseStatusEnum.DRAFT)
        self.assertEqual(
            retrieved_application["is_military_end_use_controls"], standard_application.is_military_end_use_controls,
        )
        self.assertEqual(retrieved_application["is_informed_wmd"], standard_application.is_informed_wmd)
        self.assertEqual(retrieved_application["is_suspected_wmd"], standard_application.is_suspected_wmd)
        self.assertEqual(retrieved_application["is_eu_military"], standard_application.is_eu_military)
        self.assertEqual(
            retrieved_application["is_compliant_limitations_eu"], standard_application.is_compliant_limitations_eu
        )
        self.assertEqual(retrieved_application["intended_end_use"], standard_application.intended_end_use)
        self.assertEquals(
            GoodOnApplication.objects.filter(application__id=standard_application.id).count(), 1,
        )
        self.assertEqual(
            retrieved_application["end_user"]["id"], str(standard_application.end_user.party.id),
        )
        self.assertEqual(
            retrieved_application["consignee"]["id"], str(standard_application.consignee.party.id),
        )
        self.assertEqual(
            retrieved_application["third_parties"][0]["id"], str(standard_application.third_parties.get().party.id),
        )

    @parameterized.expand([(CaseTypeEnum.EXHIBITION,), (CaseTypeEnum.GIFTING,), (CaseTypeEnum.F680,)])
    def test_view_draft_MOD_clearances_list_as_exporter_success(self, type):
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        application = self.create_mod_clearance_application(self.organisation, case_type=type)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["name"], application.name)
        self.assertEqual(
            response_data[0]["case_type"]["sub_type"]["key"], application.case_type.sub_type,
        )
        self.assertIsNotNone(response_data[0]["updated_at"])
        self.assertEqual(response_data[0]["status"]["key"], CaseStatusEnum.DRAFT)

    def test_view_draft_exhibition_clearance_as_exporter_success(self):
        application = self.create_mod_clearance_application(self.organisation, case_type=CaseTypeEnum.EXHIBITION)

        url = reverse("applications:application", kwargs={"pk": application.id})

        response = self.client.get(url, **self.exporter_headers)
        retrieved_application = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_application["name"], application.name)
        self.assertEqual(retrieved_application["case_type"]["reference"]["key"], application.case_type.reference)
        self.assertIsNotNone(retrieved_application["created_at"])
        self.assertIsNotNone(retrieved_application["updated_at"])
        self.assertIsNone(retrieved_application["submitted_at"])
        self.assertEqual(retrieved_application["title"], application.title)
        self.assertEqual(retrieved_application["first_exhibition_date"], str(application.first_exhibition_date))
        self.assertEqual(retrieved_application["required_by_date"], str(application.required_by_date))
        self.assertEqual(retrieved_application["reason_for_clearance"], application.reason_for_clearance)

        self.assertEqual(retrieved_application["status"]["key"], CaseStatusEnum.DRAFT)
        self.assertEqual(GoodOnApplication.objects.filter(application__id=application.id).count(), 1)

    def test_view_draft_gifting_clearance_as_exporter_success(self):
        application = self.create_mod_clearance_application(self.organisation, case_type=CaseTypeEnum.GIFTING)

        url = reverse("applications:application", kwargs={"pk": application.id})

        response = self.client.get(url, **self.exporter_headers)
        retrieved_application = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_application["name"], application.name)
        self.assertEqual(
            retrieved_application["case_type"]["reference"]["key"], application.case_type.reference,
        )
        self.assertIsNotNone(retrieved_application["created_at"])
        self.assertIsNotNone(retrieved_application["updated_at"])
        self.assertIsNone(retrieved_application["submitted_at"])
        self.assertEqual(retrieved_application["status"]["key"], CaseStatusEnum.DRAFT)
        self.assertEqual(GoodOnApplication.objects.filter(application__id=application.id).count(), 1)
        self.assertEqual(
            retrieved_application["end_user"]["id"], str(application.end_user.party.id),
        )
        self.assertEqual(
            retrieved_application["third_parties"][0]["id"], str(application.third_parties.get().party.id),
        )

    def test_view_draft_f680_clearance_as_exporter_success(self):
        application = self.create_mod_clearance_application(self.organisation, case_type=CaseTypeEnum.F680)

        url = reverse("applications:application", kwargs={"pk": application.id})

        response = self.client.get(url, **self.exporter_headers)
        retrieved_application = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_application["name"], application.name)
        self.assertEqual(
            retrieved_application["case_type"]["reference"]["key"], application.case_type.reference,
        )
        self.assertIsNotNone(retrieved_application["created_at"])
        self.assertIsNotNone(retrieved_application["updated_at"])
        self.assertIsNone(retrieved_application["submitted_at"])
        self.assertEqual(retrieved_application["status"]["key"], CaseStatusEnum.DRAFT)
        self.assertEqual(GoodOnApplication.objects.filter(application__id=application.id).count(), 1)
        self.assertEqual(
            retrieved_application["end_user"]["id"], str(application.end_user.party.id),
        )
        self.assertEqual(
            retrieved_application["third_parties"][0]["id"], str(application.third_parties.get().party.id),
        )

    def test_view_draft_open_application_as_exporter_success(self):
        open_application = self.create_draft_open_application(self.organisation)

        url = reverse("applications:application", kwargs={"pk": open_application.id})

        response = self.client.get(url, **self.exporter_headers)

        retrieved_application = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_application["name"], open_application.name)
        self.assertEqual(
            retrieved_application["case_type"]["reference"]["key"], open_application.case_type.reference,
        )
        self.assertEqual(retrieved_application["export_type"]["key"], open_application.export_type)
        self.assertIsNotNone(retrieved_application["created_at"])
        self.assertIsNotNone(retrieved_application["updated_at"])
        self.assertIsNone(retrieved_application["submitted_at"])
        self.assertEqual(retrieved_application["status"]["key"], CaseStatusEnum.DRAFT)
        self.assertEqual(
            retrieved_application["is_military_end_use_controls"], open_application.is_military_end_use_controls
        )
        self.assertEqual(retrieved_application["is_informed_wmd"], open_application.is_informed_wmd)
        self.assertEqual(retrieved_application["is_suspected_wmd"], open_application.is_suspected_wmd)
        self.assertEqual(retrieved_application["intended_end_use"], open_application.intended_end_use)
        self.assertIn("is_good_incorporated", retrieved_application["goods_types"][0])
        self.assertEqual(GoodsType.objects.filter(application__id=open_application.id).count(), 2)
        self.assertIsNotNone(
            CountryOnApplication.objects.filter(application__id=open_application.id).count(), 1,
        )
        self.assertEqual(
            SiteOnApplication.objects.filter(application__id=open_application.id).count(), 1,
        )

    def test_view_draft_hmrc_query_as_hmrc_exporter_success(self):
        hmrc_query = self.create_hmrc_query(self.organisation)

        url = reverse("applications:application", kwargs={"pk": hmrc_query.id})

        response = self.client.get(url, **self.hmrc_exporter_headers)

        retrieved_application = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_application["name"], hmrc_query.name)
        self.assertEqual(
            retrieved_application["case_type"]["reference"]["key"], hmrc_query.case_type.reference,
        )
        self.assertIsNotNone(retrieved_application["created_at"])
        self.assertIsNotNone(retrieved_application["updated_at"])
        self.assertIsNone(retrieved_application["submitted_at"])
        self.assertEqual(retrieved_application["status"]["key"], CaseStatusEnum.DRAFT)
        self.assertEqual(retrieved_application["organisation"]["id"], str(hmrc_query.organisation.id))
        self.assertEqual(
            retrieved_application["hmrc_organisation"]["id"], str(hmrc_query.hmrc_organisation.id),
        )
        self.assertIsNotNone(GoodsType.objects.get(application__id=hmrc_query.id))
        self.assertEqual(retrieved_application["end_user"]["id"], str(hmrc_query.end_user.party.id))
        self.assertEqual(retrieved_application["consignee"]["id"], str(hmrc_query.consignee.party.id))
        self.assertEqual(
            retrieved_application["third_parties"][0]["id"], str(hmrc_query.third_parties.get().party.id),
        )

    def test_view_nonexisting_draft_failure(self):
        invalid_id = UUID("90D6C724-0339-425A-99D2-9D2B8E864EC6")

        url = reverse("applications:application", kwargs={"pk": invalid_id}) + "?submitted=false"
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_only_sees_their_organisations_drafts_in_list(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        self.create_draft_standard_application(organisation_2)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 0)

    def test_user_cannot_see_details_of_another_organisations_draft(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        draft = self.create_draft_standard_application(organisation_2)

        url = reverse("applications:application", kwargs={"pk": draft.id}) + "?submitted=false"

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @parameterized.expand(
        [
            (CaseTypeEnum.SICL.id, DataTestClient.create_draft_standard_application),
            (CaseTypeEnum.OICL.id, DataTestClient.create_draft_open_application),
        ]
    )
    def test_trade_control_application(self, case_type_id, create_function):
        application = create_function(self, self.organisation, case_type_id=case_type_id)
        application.trade_control_activity = TradeControlActivity.OTHER
        application.trade_control_activity_other = "other activity"
        application.trade_control_product_categories = [key for key, _ in TradeControlProductCategory.choices]
        application.save()

        url = reverse("applications:application", kwargs={"pk": application.id})
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()

        trade_control_activity = response["trade_control_activity"]["value"]
        self.assertEqual(trade_control_activity, application.trade_control_activity_other)

        trade_control_product_categories = [
            category["key"] for category in response["trade_control_product_categories"]
        ]
        self.assertEqual(trade_control_product_categories, application.trade_control_product_categories)
