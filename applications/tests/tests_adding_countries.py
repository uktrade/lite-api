from django.core.management import call_command
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from applications.libraries.case_status_helpers import get_case_statuses
from applications.models import CountryOnApplication
from static.countries.helpers import get_country
from static.countries.models import Country
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class CountriesOnDraftApplicationTests(DataTestClient):
    COUNTRIES_COUNT = 10

    def setUp(self):
        super().setUp()
        self.draft = self.create_open_application(self.organisation)

        self.url = reverse("applications:countries", kwargs={"pk": self.draft.id})
        self.data = {
            "countries": Country.objects.all()[: self.COUNTRIES_COUNT].values_list(
                "id", flat=True
            )
        }

    def test_add_countries_to_a_draft_success(self):
        response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.url, **self.exporter_headers).json()
        self.assertEqual(len(response["countries"]), self.COUNTRIES_COUNT)

    def test_add_no_countries_to_a_draft_failure(self):
        data = {"countries": []}

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_countries_to_a_submitted_application_failure(self):
        self.submit_application(self.draft)
        countries_on_app_before = CountryOnApplication.objects.filter(
            application=self.draft
        ).count()

        response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            CountryOnApplication.objects.filter(application=self.draft).count(),
            countries_on_app_before,
        )

    def test_remove_countries_from_a_submitted_application_success(self):
        CountryOnApplication(application=self.draft, country=get_country("US")).save()
        self.submit_application(self.draft)
        countries_on_app_before = CountryOnApplication.objects.filter(
            application=self.draft
        ).count()
        data = {"countries": [get_country("GB").pk]}

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            CountryOnApplication.objects.filter(application=self.draft).count(),
            countries_on_app_before - 1,
        )

    def test_add_countries_to_a_draft_standard_application_failure(self):
        std_draft = self.create_standard_application(self.organisation)
        pre_test_country_count = CountryOnApplication.objects.all().count()

        url = reverse("applications:countries", kwargs={"pk": std_draft.id})

        response = self.client.post(url, self.data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            CountryOnApplication.objects.all().count(), pre_test_country_count
        )

    def test_add_countries_to_a_draft_failure(self):
        """ Test failure in adding a country that does not exist. """
        data = {"countries": ["1234"]}

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(self.url, **self.exporter_headers).json()
        self.assertEqual(len(response["countries"]), 1)

    def test_add_countries_to_another_orgs_draft_failure(self):
        """ Test that a user cannot add countries to another organisation's draft. """
        organisation_2 = self.create_organisation_with_exporter_user()
        self.draft = self.create_open_application(organisation_2)
        self.url = reverse("applications:countries", kwargs={"pk": self.draft.id})

        response = self.client.post(self.url, self.data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @parameterized.expand(get_case_statuses(read_only=True))
    def test_add_countries_to_application_in_read_only_status_failure(
        self, read_only_status
    ):
        application = self.create_open_application(self.organisation)
        application.status = get_case_status_by_status(read_only_status)
        application.save()

        url = reverse("applications:countries", kwargs={"pk": application.id})
        response = self.client.post(url, self.data, **self.exporter_headers)

        # Default Open application already has a country added
        self.assertEqual(application.application_countries.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            CaseStatusEnum.RESUBMITTED,
            CaseStatusEnum.INITIAL_CHECKS,
            CaseStatusEnum.SUBMITTED,
        ]
    )
    def test_add_countries_to_application_in_editable_status_failure(
        self, editable_status
    ):
        """ Test failure in adding a country to an application in a minor editable status. Major editing
         status of APPLICANT_EDITING is removed from the case status list. """
        application = self.create_open_application(self.organisation)
        application.status = get_case_status_by_status(editable_status)
        application.save()

        url = reverse("applications:countries", kwargs={"pk": application.id})
        response = self.client.post(url, self.data, **self.exporter_headers)

        # Default Open application already has a country added
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(application.application_countries.count(), 1)

    @parameterized.expand(get_case_statuses(read_only=False))
    def test_remove_countries_to_application_in_editable_status_success(
        self, editable_status
    ):
        add_second_country_data = {
            "countries": Country.objects.filter(id__in=("GA", "GB")).values_list(
                "id", flat=True
            )
        }

        delete_country_data = {
            "countries": Country.objects.filter(id="GA").values_list("id", flat=True)
        }

        application = self.create_open_application(self.organisation)
        # Add second country, as cannot delete last remaining country
        url = reverse("applications:countries", kwargs={"pk": application.id})
        self.client.post(url, add_second_country_data, **self.exporter_headers)
        application.status = get_case_status_by_status(editable_status)
        application.save()

        response = self.client.post(url, delete_country_data, **self.exporter_headers)

        # Assert 'GB' country removed and 'GA' country remains
        self.assertEqual(application.application_countries.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(application.application_countries.first().country.id, "GA")
