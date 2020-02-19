from django.urls import reverse
from rest_framework import status

from applications.models import GoodOnApplication
from goods.enums import GoodStatus
from goods.models import Good
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from static.units.enums import Units
from test_helpers.clients import DataTestClient
from test_helpers.helpers import is_not_verified_flag_set_on_good


class GoodTests(DataTestClient):
    def test_submitted_good_changes_status_and_adds_system_flag(self):
        """
        Test that the good's status is set to submitted and the 'is_not_verified' flag is added
        """
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        draft = self.create_draft_standard_application(self.organisation)
        self.assertEqual(Good.objects.get().status, "draft")
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response_data["application"]["status"],
            {"key": CaseStatusEnum.SUBMITTED, "value": CaseStatusEnum.get_text(CaseStatusEnum.SUBMITTED)},
        )
        good = Good.objects.get()
        self.assertEqual(good.status, GoodStatus.SUBMITTED)
        self.assertTrue(is_not_verified_flag_set_on_good(good))

    def test_submitted_good_cannot_be_edited(self):
        """
        Tests that the good cannot be edited after submission
        """
        draft = self.create_draft_standard_application(self.organisation)
        self.submit_application(application=draft)

        good = Good.objects.get()
        url = reverse("goods:good", kwargs={"pk": good.id})

        response = self.client.put(url, {}, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsubmitted_good_can_be_edited(self):
        """
        Tests that the good can be edited after submission
        """
        draft = self.create_draft_standard_application(self.organisation)
        good_on_app = GoodOnApplication.objects.get(application=draft)
        url = reverse("goods:good", kwargs={"pk": good_on_app.good.id})
        data = {"description": "some great good"}
        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Good.objects.get().description, "some great good")

    def test_submitted_good_cannot_be_deleted(self):
        """
        Tests that the good cannot be deleted after submission
        """
        draft = self.create_draft_standard_application(self.organisation)
        self.submit_application(draft)
        good = Good.objects.get()
        url = reverse("goods:good", kwargs={"pk": good.id})
        response = self.client.delete(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Good.objects.count(), 1)

    def test_unsubmitted_good_can_be_deleted(self):
        """
        Tests that the good can be deleted after submission
        """
        self.create_draft_standard_application(self.organisation)
        good = Good.objects.get()
        url = reverse("goods:good", kwargs={"pk": good.id})
        response = self.client.delete(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Good.objects.count(), 0)

    def test_deleted_good_removed_from_all_drafts_they_existed_in(self):
        """
        Tests that goods get deleted from drafts that they were assigned to, after good deletion
        """
        draft_two = self.create_draft_standard_application(self.organisation)

        good = Good.objects.get()
        GoodOnApplication(good=good, application=draft_two, quantity=10, unit=Units.NAR, value=500).save()

        self.assertEqual(Good.objects.all().count(), 1)
        self.assertEqual(GoodOnApplication.objects.count(), 2)

        url = reverse("goods:good", kwargs={"pk": good.id})
        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Good.objects.all().count(), 0)
        self.assertEqual(GoodOnApplication.objects.count(), 0)
