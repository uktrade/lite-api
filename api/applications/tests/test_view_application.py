from uuid import UUID

from django.urls import reverse
from rest_framework import status

from api.applications.models import (
    GoodOnApplication,
    SiteOnApplication,
)
from api.organisations.tests.factories import SiteFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient
from api.users.libraries.get_user import get_user_organisation_relationship


class DraftTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("applications:applications") + "?submitted=false"

    def test_view_draft_standard_application_list_as_exporter_success(self):
        """
        Ensure we can get a list of drafts.
        """
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        standard_application = self.create_draft_standard_application(self.organisation)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["name"], standard_application.name)
        self.assertEqual(response_data[0]["case_type"]["sub_type"]["key"], standard_application.case_type.sub_type)
        self.assertIsNotNone(response_data[0]["updated_at"])
        self.assertEqual(response_data[0]["status"]["key"], CaseStatusEnum.DRAFT)

    def test_ensure_user_cannot_see_applications_they_dont_have_access_to(self):
        """
        Ensure that the exporter cannot see applications with sites that they don't have access to.
        """
        self.create_draft_standard_application(self.organisation)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)

    def test_ensure_user_cannot_see_applications_they_only_have_partial_access_to_(self):
        """
        Ensure that the exporter cannot see applications with sites that they don't have access to AND
        sites that they are assigned to.
        """
        relationship = get_user_organisation_relationship(self.exporter_user, self.organisation)
        relationship.sites.set([self.organisation.primary_site])
        site_2 = SiteFactory(organisation=self.organisation)
        application = self.create_draft_standard_application(self.organisation)
        SiteOnApplication(site=site_2, application=application).save()

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 0)

    def test_view_draft_standard_application_as_exporter_success(self):
        standard_application = self.create_draft_standard_application(self.organisation)

        url = reverse("applications:application", kwargs={"pk": standard_application.id})

        response = self.client.get(url, **self.exporter_headers)

        retrieved_application = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved_application["id"], str(standard_application.id))
        self.assertEqual(retrieved_application["name"], standard_application.name)
        self.assertEqual(
            retrieved_application["case_type"]["reference"]["key"],
            standard_application.case_type.reference,
        )
        self.assertEqual(
            retrieved_application["export_type"]["key"],
            standard_application.export_type,
        )
        self.assertIsNotNone(retrieved_application["created_at"])
        self.assertIsNotNone(retrieved_application["updated_at"])
        self.assertIsNone(retrieved_application["submitted_at"])
        self.assertEqual(retrieved_application["status"]["key"], CaseStatusEnum.DRAFT)
        self.assertEqual(
            retrieved_application["is_military_end_use_controls"],
            standard_application.is_military_end_use_controls,
        )
        self.assertEqual(retrieved_application["is_informed_wmd"], standard_application.is_informed_wmd)
        self.assertEqual(retrieved_application["is_suspected_wmd"], standard_application.is_suspected_wmd)
        self.assertEqual(retrieved_application["is_eu_military"], standard_application.is_eu_military)
        self.assertEqual(
            retrieved_application["is_compliant_limitations_eu"], standard_application.is_compliant_limitations_eu
        )
        self.assertEqual(retrieved_application["intended_end_use"], standard_application.intended_end_use)
        self.assertEqual(
            GoodOnApplication.objects.filter(application__id=standard_application.id).count(),
            1,
        )
        self.assertEqual(
            retrieved_application["end_user"]["id"],
            str(standard_application.end_user.party.id),
        )
        self.assertEqual(
            retrieved_application["consignee"]["id"],
            str(standard_application.consignee.party.id),
        )
        self.assertEqual(
            retrieved_application["third_parties"][0]["id"],
            str(standard_application.third_parties.get().party.id),
        )

    def test_view_nonexisting_draft_failure(self):
        invalid_id = UUID("90D6C724-0339-425A-99D2-9D2B8E864EC6")

        url = reverse("applications:application", kwargs={"pk": invalid_id}) + "?submitted=false"
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_only_sees_their_organisations_drafts_in_list(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        self.create_draft_standard_application(organisation_2)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["results"]), 0)

    def test_user_cannot_see_details_of_another_organisations_draft(self):
        organisation_2, _ = self.create_organisation_with_exporter_user()
        draft = self.create_draft_standard_application(organisation_2)

        url = reverse("applications:application", kwargs={"pk": draft.id}) + "?submitted=false"

        response = self.client.get(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
