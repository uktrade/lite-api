from uuid import UUID

from django.urls import reverse
from rest_framework import status

from applications.models import (
    GoodOnApplication,
    CountryOnApplication,
    SiteOnApplication,
)
from goodstype.models import GoodsType
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class DraftTests(DataTestClient):
    url = reverse("applications:applications") + "?submitted=false"

    def test_view_draft_standard_application_list_as_exporter_success(self):
        """
        Ensure we can get a list of drafts.
        """
        standard_application = self.create_standard_application(self.organisation)

        response = self.client.get(self.url, **self.exporter_headers)

        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["name"], standard_application.name)
        self.assertEqual(
            response_data[0]["application_type"]["key"], standard_application.application_type,
        )
        self.assertEqual(response_data[0]["export_type"]["key"], standard_application.export_type)
        self.assertIsNotNone(response_data[0]["created"])
        self.assertIsNotNone(response_data[0]["modified"])
        self.assertIsNone(response_data[0]["submitted_at"])
        self.assertEqual(response_data[0]["status"]["key"], CaseStatusEnum.DRAFT)

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
        self.assertEqual(response_data[0]["application_type"]["key"], hmrc_query.application_type)
        self.assertEqual(response_data[0]["organisation"]["name"], hmrc_query.organisation.name)
        self.assertIsNone(response_data[0]["export_type"])
        self.assertIsNotNone(response_data[0]["created"])
        self.assertIsNotNone(response_data[0]["modified"])
        self.assertIsNone(response_data[0]["submitted_at"])
        self.assertEqual(response_data[0]["status"]["key"], CaseStatusEnum.DRAFT)

    def test_view_draft_standard_application_as_exporter_success(self):
        standard_application = self.create_standard_application(self.organisation)

        url = reverse("applications:application", kwargs={"pk": standard_application.id})

        response = self.client.get(url, **self.exporter_headers)

        retrieved_application = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_application["name"], standard_application.name)
        self.assertEqual(
            retrieved_application["application_type"]["key"], standard_application.application_type,
        )
        self.assertEqual(
            retrieved_application["export_type"]["key"], standard_application.export_type,
        )
        self.assertIsNotNone(retrieved_application["created"])
        self.assertIsNotNone(retrieved_application["modified"])
        self.assertIsNone(retrieved_application["submitted_at"])
        self.assertEqual(retrieved_application["status"]["key"], CaseStatusEnum.DRAFT)
        self.assertEquals(
            GoodOnApplication.objects.filter(application__id=standard_application.id).count(), 1,
        )
        self.assertEqual(
            retrieved_application["end_user"]["id"], str(standard_application.end_user.id),
        )
        self.assertEqual(
            retrieved_application["consignee"]["id"], str(standard_application.consignee.id),
        )
        self.assertEqual(
            retrieved_application["third_parties"][0]["id"], str(standard_application.third_parties.get().id),
        )

    def test_view_draft_open_application_as_exporter_success(self):
        open_application = self.create_open_application(self.organisation)

        url = reverse("applications:application", kwargs={"pk": open_application.id})

        response = self.client.get(url, **self.exporter_headers)

        retrieved_application = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_application["name"], open_application.name)
        self.assertEqual(
            retrieved_application["application_type"]["key"], open_application.application_type,
        )
        self.assertEqual(retrieved_application["export_type"]["key"], open_application.export_type)
        self.assertIsNotNone(retrieved_application["created"])
        self.assertIsNotNone(retrieved_application["modified"])
        self.assertIsNone(retrieved_application["submitted_at"])
        self.assertEqual(retrieved_application["status"]["key"], CaseStatusEnum.DRAFT)
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
            retrieved_application["application_type"]["key"], hmrc_query.application_type,
        )
        self.assertIsNotNone(retrieved_application["created"])
        self.assertIsNotNone(retrieved_application["modified"])
        self.assertIsNone(retrieved_application["submitted_at"])
        self.assertEqual(retrieved_application["status"]["key"], CaseStatusEnum.DRAFT)
        self.assertEqual(retrieved_application["organisation"]["id"], str(hmrc_query.organisation.id))
        self.assertEqual(
            retrieved_application["hmrc_organisation"]["id"], str(hmrc_query.hmrc_organisation.id),
        )
        self.assertIsNotNone(GoodsType.objects.get(application__id=hmrc_query.id))
        self.assertEqual(retrieved_application["end_user"]["id"], str(hmrc_query.end_user.id))
        self.assertEqual(retrieved_application["consignee"]["id"], str(hmrc_query.consignee.id))
        self.assertEqual(
            retrieved_application["third_parties"][0]["id"], str(hmrc_query.third_parties.get().id),
        )

    def test_view_nonexisting_draft_failure(self):
        invalid_id = UUID("90D6C724-0339-425A-99D2-9D2B8E864EC6")

        url = reverse("applications:application", kwargs={"pk": invalid_id}) + "?submitted=false"
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_only_sees_their_organisations_drafts_in_list(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        self.create_standard_application(organisation_2)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 0)

    def test_user_cannot_see_details_of_another_organisations_draft(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        draft = self.create_standard_application(organisation_2)

        url = reverse("applications:application", kwargs={"pk": draft.id}) + "?submitted=false"

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
