from applications.enums import GoodsCategory
from applications.enums import ApplicationExportType
from audit_trail.models import Audit
from flags.enums import SystemFlags
from lite_content.lite_api import strings
from django.urls import reverse
from rest_framework import status

from applications.models import SiteOnApplication, GoodOnApplication, PartyOnApplication
from cases.models import Case
from goods.enums import GoodStatus
from parties.enums import PartyType
from parties.models import PartyDocument
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class StandardApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_standard_application(self.organisation)
        self.url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_submit_standard_application_before_declaration_success(self):
        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get(id=self.draft.id)
        self.assertIsNone(case.submitted_at)
        self.assertEqual(case.status.status, CaseStatusEnum.DRAFT)
        for good_on_application in GoodOnApplication.objects.filter(application=case):
            self.assertEqual(good_on_application.good.status, GoodStatus.DRAFT)
        self.assertEqual(Audit.objects.all().count(), 0)

    def test_submit_standard_application_with_incorporated_good_success(self):
        draft = self.create_standard_application_with_incorporated_good(self.organisation)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get(id=draft.id)
        self.assertIsNone(case.submitted_at)
        self.assertEqual(case.status.status, CaseStatusEnum.DRAFT)

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
        self.draft.delete_party(PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.END_USER))

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
        self.draft.delete_party(self.draft.consignee)

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
        draft = self.create_draft_standard_application(self.organisation, safe_document=None)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Standard.END_USER_DOCUMENT_PROCESSING,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_status_code_post_with_infected_document_failure(self):
        draft = self.create_draft_standard_application(self.organisation, safe_document=False)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Standard.END_USER_DOCUMENT_INFECTED,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_exp_set_application_status_to_submitted_when_previously_applicant_editing_success(self):
        standard_application = self.create_draft_standard_application(self.organisation)
        self.submit_application(standard_application)
        standard_application.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        standard_application.save()
        previous_submitted_at = standard_application.submitted_at

        data = {"submit_declaration": True, "agreed_to_declaration": True, "agreed_to_foi": True}

        url = reverse("applications:application_submit", kwargs={"pk": standard_application.id})

        response = self.client.put(url, data, **self.exporter_headers)

        standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            standard_application.status, get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )
        self.assertNotEqual(standard_application.submitted_at, previous_submitted_at)
        self.assertEqual(standard_application.agreed_to_foi, True)

    def test_exp_set_application_status_to_submitted_when_previously_not_applicant_editing_failure(self):
        standard_application = self.create_draft_standard_application(self.organisation)
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

    def test_submit_standard_application_without_end_use_details_failure(self):
        self.draft.intended_end_use = ""
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response, text=strings.Applications.Generic.NO_END_USE_DETAILS, status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_standard_application_declaration_submit_success(self):
        self.draft.agreed_to_foi = True
        self.draft.save()

        data = {"submit_declaration": True, "agreed_to_declaration": True, "agreed_to_foi": True}

        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        case = Case.objects.get(id=self.draft.id)
        self.assertIsNotNone(case.submitted_at)
        self.assertEqual(case.status.status, CaseStatusEnum.SUBMITTED)
        self.assertEqual(case.baseapplication.agreed_to_foi, True)
        for good_on_application in GoodOnApplication.objects.filter(application=case):
            self.assertEqual(good_on_application.good.status, GoodStatus.SUBMITTED)
        self.assertEqual(Audit.objects.all().count(), 1)

    def test_standard_application_declaration_submit_tcs_false_failure(self):
        data = {"submit_declaration": True, "agreed_to_declaration": False, "agreed_to_foi": True}

        url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()["errors"]
        self.assertEqual(errors["agreed_to_declaration"], [strings.Applications.Generic.AGREEMENT_TO_TCS_REQUIRED])

    def test_submit_standard_application_adds_system_case_flags_success(self):
        self.draft.is_military_end_use_controls = True
        self.draft.is_informed_wmd = True
        self.draft.goods_categories = [GoodsCategory.MARITIME_ANTI_PIRACY, GoodsCategory.FIREARMS]
        self.draft.save()
        data = {"submit_declaration": True, "agreed_to_declaration": True, "agreed_to_foi": True}

        response = self.client.put(self.url, data=data, **self.exporter_headers)
        self.draft.refresh_from_db()
        case_flags = [str(flag_id) for flag_id in self.draft.flags.values_list("id", flat=True)]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(SystemFlags.MILITARY_END_USE_ID, case_flags)
        self.assertIn(SystemFlags.WMD_END_USE_ID, case_flags)
        self.assertIn(SystemFlags.MARITIME_ANTI_PIRACY_ID, case_flags)
        self.assertIn(SystemFlags.FIREARMS_ID, case_flags)

    def test_resubmit_edited_standard_application_removes_system_case_flags_success(self):
        # Create draft application with properties that have associated system flags
        self.draft.is_military_end_use_controls = True
        self.draft.is_suspected_wmd = True
        self.draft.goods_categories = [GoodsCategory.MARITIME_ANTI_PIRACY, GoodsCategory.FIREARMS]
        self.draft.save()

        # Submit application (this function also adds system flags)
        self.submit_application(self.draft)

        # Set application status to 'Applicant Editing'
        self.draft.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.draft.save()

        # Update application properties
        self.draft.is_military_end_use_controls = False
        self.draft.is_suspected_wmd = False
        self.draft.goods_categories = None
        self.draft.save()

        # Re-submit application
        data = {"submit_declaration": True, "agreed_to_declaration": True, "agreed_to_foi": True}
        response = self.client.put(self.url, data=data, **self.exporter_headers)
        self.draft.refresh_from_db()
        case_flags = [str(flag_id) for flag_id in self.draft.flags.values_list("id", flat=True)]

        # Assert flags have been removed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(SystemFlags.MILITARY_END_USE_ID, case_flags)
        self.assertNotIn(SystemFlags.WMD_END_USE_ID, case_flags)
        self.assertNotIn(SystemFlags.MARITIME_ANTI_PIRACY_ID, case_flags)
        self.assertNotIn(SystemFlags.FIREARMS_ID, case_flags)

    def test_submit_standard_application_temporary_with_temp_export_details_success(self):
        self.draft.export_type = ApplicationExportType.TEMPORARY
        self.draft.temp_export_details = "reasons why this export is a temporary one"
        self.draft.is_temp_direct_control = False
        self.draft.proposed_return_date = "2020-05-11"
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_submit_standard_application_temporary_without_temp_export_details_failure(self):
        self.draft.export_type = ApplicationExportType.TEMPORARY
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Generic.NO_TEMPORARY_EXPORT_DETAILS,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_submit_standard_application_temporary_with_partial_temp_export_details_failure(self):
        self.draft.export_type = ApplicationExportType.TEMPORARY
        self.draft.temp_export_details = "reasons why this export is a temporary one"
        self.draft.proposed_return_date = "2020-05-11"
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertContains(
            response,
            text=strings.Applications.Generic.NO_TEMPORARY_EXPORT_DETAILS,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
