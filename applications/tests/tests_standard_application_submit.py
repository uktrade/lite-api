from audit_trail.models import Audit
from lite_content.lite_api import strings
from django.urls import reverse
from rest_framework import status

from applications.models import SiteOnApplication, GoodOnApplication, PartyOnApplication
from cases.models import Case
from goods.enums import GoodStatus
from parties.enums import PartyType
from parties.models import PartyDocument, Party
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class StandardApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_application(self.organisation)
        self.url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_submit_standard_application_success(self):
        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get(id=self.draft.id)
        self.assertIsNotNone(case.submitted_at)
        self.assertEqual(case.status.status, CaseStatusEnum.SUBMITTED)
        for good_on_application in GoodOnApplication.objects.filter(application=case):
            self.assertEqual(good_on_application.good.status, GoodStatus.SUBMITTED)
        # 'Draft' applications should not create audit entries when submitted
        self.assertEqual(Audit.objects.all().count(), 0)

    def test_submit_standard_application_with_incorporated_good_success(self):
        draft = self.create_standard_application_with_incorporated_good(self.organisation)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get(id=draft.id)
        self.assertIsNotNone(case.submitted_at)
        self.assertEqual(case.status.status, CaseStatusEnum.SUBMITTED)

    def test_submit_standard_application_with_invalid_id_failure(self):
        draft_id = "90D6C724-0339-425A-99D2-9D2B8E864EC7"
        url = "applications/" + draft_id + "/submit/"

        response = self.client.put(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_standard_application_without_site_or_external_location_failure(self):
        SiteOnApplication.objects.get(application=self.draft).delete()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response, text=strings.Applications.Generic.NO_LOCATION_SET, status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_standard_application_without_end_user_failure(self):
        PartyOnApplication.objects.filter(application=self.draft, party__type=PartyType.END_USER).delete()

        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response, text=strings.Applications.Standard.NO_END_USER_SET, status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_standard_application_without_end_user_document_failure(self):
        PartyDocument.objects.filter(party=self.draft.end_user.party).delete()

        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Standard.NO_END_USER_DOCUMENT_SET,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_standard_application_without_consignee_failure(self):
        PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.CONSIGNEE).delete()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response, text=strings.Applications.Standard.NO_CONSIGNEE_SET, status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_standard_application_without_consignee_document_failure(self):
        PartyDocument.objects.filter(party=self.draft.consignee.party).delete()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Standard.NO_CONSIGNEE_DOCUMENT_SET,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_standard_application_without_good_failure(self):
        GoodOnApplication.objects.get(application=self.draft).delete()
        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response, text=strings.Applications.Standard.NO_GOODS_SET, status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_draft_with_incorporated_good_and_without_ultimate_end_users_failure(self):
        """
        This should be unsuccessful as an ultimate end user is required when
        there is a part which is to be incorporated into another good
        """
        draft = self.create_standard_application_with_incorporated_good(self.organisation)
        PartyOnApplication.objects.filter(application=draft, party__type=PartyType.ULTIMATE_END_USER).delete()
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Standard.NO_ULTIMATE_END_USERS_SET,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_draft_with_incorporated_good_and_without_ultimate_end_user_documents_failure(self):
        draft = self.create_standard_application_with_incorporated_good(self.organisation)
        PartyDocument.objects.filter(party__in=draft.ultimate_end_users.all().values("party")).delete()
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Standard.NO_ULTIMATE_END_USER_DOCUMENT_SET,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_status_code_post_with_untested_document_failure(self):
        draft = self.create_standard_application(self.organisation, safe_document=None)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Standard.END_USER_DOCUMENT_PROCESSING,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_status_code_post_with_infected_document_failure(self):
        draft = self.create_standard_application(self.organisation, safe_document=False)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Standard.END_USER_DOCUMENT_INFECTED,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_exp_set_application_status_to_submitted_when_previously_applicant_editing_success(self):
        standard_application = self.create_standard_application(self.organisation)
        self.submit_application(standard_application)
        standard_application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        standard_application.save()
        previous_submitted_at = standard_application.submitted_at

        url = reverse("applications:application_submit", kwargs={"pk": standard_application.id})
        response = self.client.put(url, **self.exporter_headers)

        standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )
        self.assertNotEqual(standard_application.submitted_at, previous_submitted_at)

    def test_exp_set_application_status_to_submitted_when_previously_not_applicant_editing_failure(self):
        standard_application = self.create_standard_application(self.organisation)
        standard_application.status = get_case_status_by_status(CaseStatusEnum.INITIAL_CHECKS)
        standard_application.save()
        previous_submitted_at = standard_application.submitted_at

        url = reverse("applications:application_submit", kwargs={"pk": standard_application.id})
        response = self.client.put(url, **self.exporter_headers)

        standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            standard_application.status, get_case_status_by_status(CaseStatusEnum.INITIAL_CHECKS),
        )
        self.assertEqual(standard_application.submitted_at, previous_submitted_at)

    def test_submit_standard_application_and_verified_good_status_is_not_altered(self):
        for good_on_application in GoodOnApplication.objects.filter(application=self.draft):
            good_on_application.good.status = GoodStatus.VERIFIED
            good_on_application.good.save()

        response = self.client.put(self.url, **self.exporter_headers)

        case = Case.objects.get()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for good_on_application in GoodOnApplication.objects.filter(application=case):
            self.assertEqual(good_on_application.good.status, GoodStatus.VERIFIED)

    def test_cannot_submit_application_without_permission(self):
        self.exporter_user.set_role(self.organisation, self.exporter_default_role)
        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
