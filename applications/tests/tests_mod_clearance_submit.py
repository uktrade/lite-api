from django.urls import reverse
from parameterized import parameterized_class
from rest_framework import status

from applications.enums import ApplicationType
from applications.models import SiteOnApplication, GoodOnApplication
from parties.models import PartyDocument
from test_helpers.clients import DataTestClient
from lite_content.lite_api import strings


@parameterized_class(
    "application_type",
    [
        (ApplicationType.EXHIBITION_CLEARANCE,),
        (ApplicationType.GIFTING_CLEARANCE,),
        (ApplicationType.F_680_CLEARANCE,),
    ],
)
class MODClearanceTests(DataTestClient):
    """ Shared MOD clearance tests """

    def setUp(self):
        super().setUp()
        self.draft = self.create_mod_clearance_application(self.organisation, type=self.application_type)
        self.url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_submit_MOD_clearance_success(self):
        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["application"]["name"], self.draft.name)

    def test_submit_MOD_clearance_without_location_failure(self):
        SiteOnApplication.objects.get(application=self.draft).delete()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"]["location"], strings.Applications.Generic.NO_LOCATION_SET)

    def test_submit_MOD_clearance_without_goods_failure(self):
        GoodOnApplication.objects.get(application=self.draft).delete()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"]["goods"], strings.Applications.Standard.NO_GOODS_SET)

    def test_submit_MOD_clearance_without_parties_failure(self):
        self.draft.end_user = None
        self.draft.third_parties.get_queryset().delete()
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)
        errors = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        if "end_user" in errors:
            self.assertEqual(errors["end_user"], strings.Applications.Standard.NO_END_USER_SET)
        else:
            self.assertEqual(errors["party"], strings.Applications.F680.NO_END_USER_OR_THIRD_PARTY)


class GiftingClearanceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_mod_clearance_application(self.organisation, type=ApplicationType.GIFTING_CLEARANCE)
        self.url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)

    def test_submit_gifting_clearance_success(self):
        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["application"]["name"], self.draft.name)

    def test_submit_gifting_clearance_without_end_user_failure(self):
        self.draft.end_user = None
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"]["end_user"], strings.Applications.Standard.NO_END_USER_SET)

    def test_submit_gifting_clearance_without_end_user_document_failure(self):
        PartyDocument.objects.filter(party=self.draft.end_user).delete()

        response = self.client.put(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"]["end_user"], strings.Applications.Standard.NO_END_USER_DOCUMENT_SET)
