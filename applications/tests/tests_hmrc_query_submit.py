from django.urls import reverse
from rest_framework import status

from cases.enums import CaseType
from cases.models import Case
from content_strings.strings import get_string
from goodstype.models import GoodsType
from parties.document.models import PartyDocument
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class HmrcQueryTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_hmrc_query(self.organisation)
        self.url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

    def test_submit_hmrc_query_success(self):
        response = self.client.put(self.url, **self.hmrc_exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get()
        self.assertEqual(case.id, self.draft.id)
        self.assertIsNotNone(case.submitted_at)
        self.assertEqual(case.status.status, CaseStatusEnum.SUBMITTED)
        self.assertEqual(case.type, CaseType.HMRC_QUERY)

    def test_submit_hmrc_query_with_invalid_id_failure(self):
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"
        url = "applications/" + draft_id + "/submit/"

        response = self.client.put(url, **self.hmrc_exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_hmrc_query_without_end_user_failure(self):
        self.draft.end_user = None
        self.draft.save()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.hmrc_exporter_headers)

        self.assertContains(
            response, text=get_string("applications.standard.no_end_user_set"), status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_hmrc_query_without_end_user_document_failure(self):
        PartyDocument.objects.filter(party=self.draft.end_user).delete()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.hmrc_exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.no_end_user_document_set"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_hmrc_query_without_goods_type_failure(self):
        GoodsType.objects.filter(application=self.draft).delete()

        response = self.client.put(self.url, **self.hmrc_exporter_headers)

        self.assertContains(
            response, text=get_string("applications.open.no_goods_set"), status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_status_code_post_with_untested_document_failure(self):
        draft = self.create_hmrc_query(self.organisation, safe_document=None)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.hmrc_exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.end_user_document_processing"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_status_code_post_with_infected_document_failure(self):
        draft = self.create_hmrc_query(self.organisation, safe_document=False)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.hmrc_exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.end_user_document_infected"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
