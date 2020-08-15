from django.urls import reverse
from rest_framework import status

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from cases.enums import CaseTypeEnum
from cases.models import CaseType
from api.conf.constants import GovPermissions
from api.licences.enums import LicenceStatus
from api.licences.models import Licence
from lite_content.lite_api.strings import Cases
from api.open_general_licences.tests.factories import OpenGeneralLicenceCaseFactory, OpenGeneralLicenceFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class ReissueOGELTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.gov_user.role.permissions.set([GovPermissions.REOPEN_CLOSED_CASES.name])
        open_general_licence = OpenGeneralLicenceFactory(case_type=CaseType.objects.get(id=CaseTypeEnum.OGEL.id))
        self.case = OpenGeneralLicenceCaseFactory(
            open_general_licence=open_general_licence,
            site=self.organisation.primary_site,
            organisation=self.organisation,
        )
        self.url = reverse("cases:reissue_ogl", kwargs={"pk": self.case.id})

    def test_reissue_invalid_ogel_id_failure(self):
        case = self.create_open_application_case(self.organisation)
        url = reverse("cases:reissue_ogl", kwargs={"pk": case.id})

        response = self.client.post(url, {}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reissue_existing_active_licence_failure(self):
        response = self.client.post(self.url, {}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["errors"]["confirm"], [Cases.ReissueOGEL.ERROR])

    def test_reissue_with_no_active_licence_success(self):
        # Suspend the current case/licence
        response = self.client.patch(
            reverse("cases:case", kwargs={"pk": self.case.id}), {"status": CaseStatusEnum.SUSPENDED}, **self.gov_headers
        )

        self.case.refresh_from_db()
        old_licence = Licence.objects.get(case=self.case)
        self.assertEqual(self.case.status.status, CaseStatusEnum.SUSPENDED)
        self.assertEqual(old_licence.status, LicenceStatus.SUSPENDED)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Reissue
        response = self.client.post(self.url, {}, **self.gov_headers)
        self.case.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        licence_id = response.json()["licence"]
        new_licence = Licence.objects.get(id=licence_id)
        self.assertEqual(new_licence.status, LicenceStatus.REINSTATED)
        self.assertEqual(self.case.status.status, CaseStatusEnum.FINALISED)
        self.assertEqual(Audit.objects.filter(verb=AuditType.OGEL_REISSUED, target_object_id=self.case.id).count(), 1)
