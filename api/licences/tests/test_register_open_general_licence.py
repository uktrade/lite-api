from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized
from rest_framework import status

from api.cases.enums import CaseTypeEnum
from api.cases.models import CaseType
from api.licences.enums import LicenceStatus
from api.licences.models import Licence
from api.open_general_licences.enums import OpenGeneralLicenceStatus
from api.open_general_licences.models import OpenGeneralLicenceCase
from api.open_general_licences.tests.factories import OpenGeneralLicenceFactory, OpenGeneralLicenceCaseFactory
from test_helpers.clients import DataTestClient


class RegisterOpenGeneralLicenceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("licences:open_general_licences")
        self.open_general_licence = OpenGeneralLicenceFactory(case_type=CaseType.objects.get(id=CaseTypeEnum.OGTCL.id))
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_register_open_general_licence_success(self):
        data = {
            "open_general_licence": str(self.open_general_licence.id),
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqualIgnoreType(response_data["open_general_licence"], self.open_general_licence.id)
        self.assertEqual(response_data["registrations"], [str(OpenGeneralLicenceCase.objects.get().id)])
        self.assertEqual(OpenGeneralLicenceCase.objects.count(), 1)
        ogl_case = OpenGeneralLicenceCase.objects.get()
        self.assertTrue(
            Licence.objects.filter(
                reference_code=f"{ogl_case.reference_code}",
                case=ogl_case,
                status=LicenceStatus.ISSUED,
                start_date=timezone.now().date(),
                duration__isnull=False,
            ).exists()
        )

    @parameterized.expand(
        [
            ("status", OpenGeneralLicenceStatus.DEACTIVATED),  # Can't register deactivated OGLs
            ("registration_required", False),  # Can't register OGLs that don't require registration
        ]
    )
    def test_register_open_general_licence_failure(self, param, value):
        setattr(self.open_general_licence, param, value)
        self.open_general_licence.save()

        data = {
            "open_general_licence": str(self.open_general_licence.id),
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(OpenGeneralLicenceCase.objects.count(), 0)

    def test_register_existing_open_general_licence_does_nothing(self):
        OpenGeneralLicenceCaseFactory(
            open_general_licence=self.open_general_licence,
            site=self.organisation.primary_site,
            organisation=self.organisation,
        )

        data = {
            "open_general_licence": str(self.open_general_licence.id),
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqualIgnoreType(response_data["open_general_licence"], self.open_general_licence.id)
        self.assertEqual(OpenGeneralLicenceCase.objects.count(), 1)
