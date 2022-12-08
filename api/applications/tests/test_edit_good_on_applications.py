from django.urls import reverse

from rest_framework import status

from api.applications.libraries.case_status_helpers import get_case_statuses
from api.applications.enums import NSGListType
from api.goods.tests.factories import FirearmFactory
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient


class EditGoodOnApplicationsTests(DataTestClient):
    def test_edit_a_good_on_applicaton(self):
        self.create_draft_standard_application(self.organisation)
        self.good_on_application.firearm_details = FirearmFactory.create()
        self.good_on_application.save()

        url = reverse(
            "applications:good_on_application",
            kwargs={"obj_pk": self.good_on_application.id},
        )

        response = self.client.put(
            url,
            data={
                "firearm_details": {
                    "year_of_manufacture": 1990,
                    "calibre": "1mm",
                },
            },
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.good_on_application.refresh_from_db()
        self.assertEqual(
            self.good_on_application.firearm_details.year_of_manufacture,
            1990,
        )
        self.assertEqual(
            self.good_on_application.firearm_details.calibre,
            "1mm",
        )

    def test_edit_a_good_on_applicaton_read_only(self):
        application = self.create_draft_standard_application(self.organisation)
        uneditable_status = get_case_statuses(read_only=True)[0]
        application.status = get_case_status_by_status(uneditable_status)
        application.save()

        self.good_on_application.firearm_details = FirearmFactory.create()
        self.good_on_application.save()

        original_year_of_manufacture = self.good_on_application.firearm_details.year_of_manufacture
        original_calibre = self.good_on_application.firearm_details.calibre

        url = reverse(
            "applications:good_on_application",
            kwargs={"obj_pk": self.good_on_application.id},
        )

        response = self.client.put(
            url,
            data={
                "firearm_details": {
                    "year_of_manufacture": 1990,
                    "calibre": "1mm",
                },
            },
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"errors": [strings.Applications.Generic.READ_ONLY]})

        self.good_on_application.refresh_from_db()
        self.assertEqual(
            self.good_on_application.firearm_details.year_of_manufacture,
            original_year_of_manufacture,
        )
        self.assertEqual(
            self.good_on_application.firearm_details.calibre,
            original_calibre,
        )

    def test_edit_a_good_on_applicaton_invalid_organisation(self):
        another_organisation, _ = self.create_organisation_with_exporter_user()
        application = self.create_draft_standard_application(another_organisation)
        application.save()

        self.good_on_application.firearm_details = FirearmFactory.create()
        self.good_on_application.save()

        original_year_of_manufacture = self.good_on_application.firearm_details.year_of_manufacture
        original_calibre = self.good_on_application.firearm_details.calibre

        url = reverse(
            "applications:good_on_application",
            kwargs={"obj_pk": self.good_on_application.id},
        )

        response = self.client.put(
            url,
            data={
                "firearm_details": {
                    "year_of_manufacture": 1990,
                    "calibre": "1mm",
                },
            },
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {"errors": [strings.Applications.Generic.INVALID_ORGANISATION]})

        self.good_on_application.refresh_from_db()
        self.assertEqual(
            self.good_on_application.firearm_details.year_of_manufacture,
            original_year_of_manufacture,
        )
        self.assertEqual(
            self.good_on_application.firearm_details.calibre,
            original_calibre,
        )


class GovUserEditGoodOnApplicationsTests(DataTestClient):
    def test_edit_nsg_list_type_and_NCA(self):
        self.create_draft_standard_application(self.organisation)

        url = reverse(
            "applications:good_on_application",
            kwargs={"obj_pk": self.good_on_application.id},
        )

        response = self.client.put(
            url,
            data={
                "nsg_list_type": NSGListType.TRIGGER_LIST,
                "is_nca_applicable": True,
                "nsg_assessment_note": "Trigger list product",
            },
            **self.gov_headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        self.assertEqual(response["nsg_list_type"]["key"], NSGListType.TRIGGER_LIST)
        self.assertEqual(response["is_nca_applicable"], True)
        self.assertEqual(response["nsg_assessment_note"], "Trigger list product")
