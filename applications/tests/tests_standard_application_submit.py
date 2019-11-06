from django.urls import reverse
from rest_framework import status

from applications.models import SiteOnApplication, GoodOnApplication
from cases.models import Case
from content_strings.strings import get_string
from goods.enums import GoodStatus
from parties.document.models import PartyDocument
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class StandardApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_application(self.organisation)
        self.url = reverse(
            "applications:application_submit", kwargs={"pk": self.draft.id}
        )

    def test_submit_standard_application_success(self):
        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get()
        self.assertEqual(case.application.id, self.draft.id)
        self.assertIsNotNone(case.application.submitted_at)
        self.assertEqual(case.application.status.status, CaseStatusEnum.SUBMITTED)
        for good_on_application in GoodOnApplication.objects.filter(
            application=case.application
        ):
            self.assertEqual(good_on_application.good.status, GoodStatus.SUBMITTED)

    def test_submit_standard_application_with_incorporated_good_success(self):
        draft = self.create_standard_application_with_incorporated_good(
            self.organisation
        )
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get()
        self.assertEqual(case.application.id, draft.id)
        self.assertIsNotNone(case.application.submitted_at)
        self.assertEqual(case.application.status.status, CaseStatusEnum.SUBMITTED)

    def test_submit_standard_application_with_invalid_id_failure(self):
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"
        url = "applications/" + draft_id + "/submit/"

        response = self.client.put(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_standard_application_without_site_or_external_location_failure(
        self,
    ):
        SiteOnApplication.objects.get(application=self.draft).delete()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.generic.no_location_set"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_standard_application_without_end_user_failure(self):
        self.draft.end_user = None
        self.draft.save()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.no_end_user_set"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_standard_application_without_end_user_document_failure(self):
        PartyDocument.objects.filter(party=self.draft.end_user).delete()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.no_end_user_document_set"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_standard_application_without_consignee_failure(self):
        self.draft.consignee = None
        self.draft.save()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.no_consignee_set"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_standard_application_without_consignee_document_failure(self):
        PartyDocument.objects.filter(party=self.draft.consignee).delete()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.no_consignee_document_set"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_standard_application_without_good_failure(self):
        GoodOnApplication.objects.get(application=self.draft).delete()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.no_goods_set"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_draft_with_incorporated_good_and_without_ultimate_end_users_failure(
        self,
    ):
        """
        This should be unsuccessful as an ultimate end user is required when
        there is a part which is to be incorporated into another good
        """
        draft = self.create_standard_application_with_incorporated_good(
            self.organisation
        )
        draft.ultimate_end_users.set([])
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.no_ultimate_end_users_set"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_draft_with_incorporated_good_and_without_ultimate_end_user_documents_failure(
        self,
    ):
        draft = self.create_standard_application_with_incorporated_good(
            self.organisation
        )
        for ueu in draft.ultimate_end_users.all():
            PartyDocument.objects.filter(party=ueu).delete()
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.no_ultimate_end_user_document_set"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_status_code_post_with_untested_document_failure(self):
        draft = self.create_standard_application(self.organisation, safe_document=None)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.end_user_document_processing"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_status_code_post_with_infected_document_failure(self):
        draft = self.create_standard_application(self.organisation, safe_document=False)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=get_string("applications.standard.end_user_document_infected"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_exp_set_application_status_to_submitted_when_previously_applicant_editing_success(
        self,
    ):
        standard_application = self.create_standard_application(self.organisation)
        self.submit_application(standard_application)
        standard_application.status = get_case_status_by_status(
            CaseStatusEnum.APPLICANT_EDITING
        )
        standard_application.save()
        previous_submitted_at = standard_application.submitted_at

        url = reverse(
            "applications:application_submit", kwargs={"pk": standard_application.id}
        )
        response = self.client.put(url, **self.exporter_headers)

        standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            standard_application.status,
            get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )
        self.assertNotEqual(standard_application.submitted_at, previous_submitted_at)

    def test_exp_set_application_status_to_submitted_when_previously_not_applicant_editing_failure(
        self,
    ):
        standard_application = self.create_standard_application(self.organisation)
        standard_application.status = get_case_status_by_status(
            CaseStatusEnum.MORE_INFORMATION_REQUIRED
        )
        standard_application.save()
        previous_submitted_at = standard_application.submitted_at

        url = reverse(
            "applications:application_submit", kwargs={"pk": standard_application.id}
        )
        response = self.client.put(url, **self.exporter_headers)

        standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            standard_application.status,
            get_case_status_by_status(CaseStatusEnum.MORE_INFORMATION_REQUIRED),
        )
        self.assertEqual(standard_application.submitted_at, previous_submitted_at)

    def test_submit_standard_application_and_verified_good_status_is_not_altered(self):
        for good_on_application in GoodOnApplication.objects.filter(
            application=self.draft
        ):
            good_on_application.good.status = GoodStatus.VERIFIED
            good_on_application.good.save()

        response = self.client.put(self.url, **self.exporter_headers)

        case = Case.objects.get()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for good_on_application in GoodOnApplication.objects.filter(
            application=case.application
        ):
            self.assertEqual(good_on_application.good.status, GoodStatus.VERIFIED)
