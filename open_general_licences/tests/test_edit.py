from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from api.audit_trail.models import Audit
from cases.enums import CaseTypeEnum
from cases.models import CaseType
from open_general_licences.enums import OpenGeneralLicenceStatus
from open_general_licences.tests.factories import OpenGeneralLicenceFactory
from test_helpers.clients import DataTestClient


class TestEditOGL(DataTestClient):
    def setUp(self):
        super().setUp()
        case_type = CaseType.objects.get(id=CaseTypeEnum.OGTCL.id)
        self.ogl = OpenGeneralLicenceFactory(case_type=case_type)
        self.url = reverse("open_general_licences:detail", kwargs={"pk": self.ogl.id})
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

    @parameterized.expand(
        [
            ("name", "edited name"),
            ("description", "edited description"),
            ("url", "https://www.gov.uk/government/publications/open-general-export-licence-low-value-shipments"),
            ("countries", ["AO", "AF"]),
            ("control_list_entries", ["ML3a", "5A002a1"]),
            ("registration_required", False),
            ("status", OpenGeneralLicenceStatus.DEACTIVATED),
        ]
    )
    def test_edit_fields(self, field, data):
        request_data = {field: data}

        response = self.client.patch(self.url, request_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Audit.objects.all().count(), 1)
