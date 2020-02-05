from django.urls import reverse
from rest_framework import status

from applications.models import SiteOnApplication, ExternalLocationOnApplication
from cases.enums import CaseTypeEnum
from cases.models import Case
from goodstype.models import GoodsType
from lite_content.lite_api import strings
from parties.models import PartyDocument
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class HmrcQueryTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.hmrc_query = self.create_hmrc_query(self.organisation)
        self.url = reverse("applications:application_submit", kwargs={"pk": self.hmrc_query.id})

    def test_submit_hmrc_query_success(self):
        response = self.client.put(self.url, **self.hmrc_exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get()
        self.assertEqual(case.id, self.hmrc_query.id)
        self.assertIsNotNone(case.submitted_at)
        self.assertEqual(case.status.status, CaseStatusEnum.SUBMITTED)
        self.assertEqual(case.type, CaseTypeEnum.HMRC_QUERY)

    def test_submit_hmrc_query_with_goods_departed_success(self):
        SiteOnApplication.objects.get(application=self.hmrc_query).delete()
        self.hmrc_query.have_goods_departed = True
        self.hmrc_query.save()

        response = self.client.put(self.url, **self.hmrc_exporter_headers)
        response_data = response.json()["application"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["have_goods_departed"], True)

    def test_submit_hmrc_query_with_invalid_id_failure(self):
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"
        url = "applications/" + draft_id + "/submit/"

        response = self.client.put(url, **self.hmrc_exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_hmrc_query_without_end_user_failure(self):
        self.hmrc_query.end_user = None
        self.hmrc_query.save()
        url = reverse("applications:application_submit", kwargs={"pk": self.hmrc_query.id})

        response = self.client.put(url, **self.hmrc_exporter_headers)

        self.assertContains(
            response, text=strings.Applications.Standard.NO_END_USER_SET, status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_hmrc_query_without_end_user_document_failure(self):
        PartyDocument.objects.filter(party=self.hmrc_query.end_user).delete()
        url = reverse("applications:application_submit", kwargs={"pk": self.hmrc_query.id})

        response = self.client.put(url, **self.hmrc_exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Standard.NO_END_USER_DOCUMENT_SET,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_hmrc_query_without_goods_type_failure(self):
        GoodsType.objects.filter(application=self.hmrc_query).delete()

        response = self.client.put(self.url, **self.hmrc_exporter_headers)

        self.assertContains(
            response, text=strings.Applications.Open.NO_GOODS_SET, status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_status_code_post_with_untested_document_failure(self):
        draft = self.create_hmrc_query(self.organisation, safe_document=None)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.hmrc_exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Standard.END_USER_DOCUMENT_PROCESSING,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_status_code_post_with_infected_document_failure(self):
        draft = self.create_hmrc_query(self.organisation, safe_document=False)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.hmrc_exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Standard.END_USER_DOCUMENT_INFECTED,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_setting_have_goods_departed_success(self):
        """
        Ensure that when setting have_goods_departed to True
        that it deletes all existing sites and locations on that application
        """
        data = {"have_goods_departed": True}

        response = self.client.put(
            reverse("applications:application", kwargs={"pk": self.hmrc_query.id}), data, **self.hmrc_exporter_headers
        )
        self.hmrc_query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.hmrc_query.have_goods_departed)
        self.assertEqual(SiteOnApplication.objects.filter(application=self.hmrc_query).count(), 0)
        self.assertEqual(ExternalLocationOnApplication.objects.filter(application=self.hmrc_query).count(), 0)

    def test_setting_have_goods_departed_to_false_success(self):
        """
        Ensure that when setting have_goods_departed to False that it doesn't
        delete all existing sites and locations on that application
        """
        data = {"have_goods_departed": False}

        response = self.client.put(
            reverse("applications:application", kwargs={"pk": self.hmrc_query.id}), data, **self.hmrc_exporter_headers
        )
        self.hmrc_query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.hmrc_query.have_goods_departed)
        self.assertEqual(SiteOnApplication.objects.filter(application=self.hmrc_query).count(), 1)

    def test_setting_sites_when_goods_departed_is_set_to_true_failure(self):
        """
        Ensure that it is not possible to add sites to the application
        when have_goods_departed is set to True
        """
        SiteOnApplication.objects.get(application=self.hmrc_query).delete()
        self.hmrc_query.have_goods_departed = True
        self.hmrc_query.save()

        data = {"sites": [self.hmrc_organisation.primary_site.id]}

        response = self.client.post(
            reverse("applications:application_sites", kwargs={"pk": self.hmrc_query.id}),
            data,
            **self.hmrc_exporter_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_setting_locations_when_goods_departed_is_set_to_true_failure(self):
        """
        Ensure that it is not possible to add external locations
        to the application when have_goods_departed is set to True
        """
        SiteOnApplication.objects.get(application=self.hmrc_query).delete()
        self.hmrc_query.have_goods_departed = True
        self.hmrc_query.save()
        external_location = self.create_external_location("storage facility", self.hmrc_organisation)

        data = {"external_locations": [external_location.id]}

        response = self.client.post(
            reverse("applications:application_external_locations", kwargs={"pk": self.hmrc_query.id}),
            data,
            **self.hmrc_exporter_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
