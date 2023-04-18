from unittest import mock

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.applications.models import PartyOnApplication
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from lite_content.lite_api.strings import PartyErrors
from api.parties.enums import PartyType, SubType
from api.parties.models import Party
from api.parties.models import PartyDocument
from api.staticdata.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class EndUserOnDraftTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_standard_application(self.organisation)
        self.url = reverse("applications:parties", kwargs={"pk": self.draft.id})
        self.new_end_user_data = {
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "signatory_name_euu": "Government of Paraguay",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "type": PartyType.END_USER,
        }

        self.document_url = reverse(
            "applications:party_document", kwargs={"pk": self.draft.id, "party_pk": self.draft.end_user.party.id}
        )

        self.new_document_data = {
            "name": "updated_document_name.pdf",
            "s3_key": "s3_keykey.pdf",
            "size": 123456,
        }

    @parameterized.expand([SubType.GOVERNMENT, SubType.COMMERCIAL, SubType.OTHER])
    def test_set_end_user_on_draft_standard_application_successful(self, data_type):
        data = {
            "name": "Government",
            "address": "Westminster, London SW1A 0AA",
            "signatory_name_euu": "Government",
            "country": "GB",
            "sub_type": data_type,
            "website": "https://www.gov.uk",
            "type": PartyType.END_USER,
        }

        if data_type == SubType.OTHER:
            data["sub_type_other"] = "Other"

        response = self.client.post(self.url, data, **self.exporter_headers)

        party_on_application = PartyOnApplication.objects.get(
            application=self.draft,
            party__type=PartyType.END_USER,
            deleted_at__isnull=True,
        )

        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(party_on_application.party.name, data["name"])
        self.assertEqual(party_on_application.party.address, data["address"])
        self.assertEqual(party_on_application.party.signatory_name_euu, data["signatory_name_euu"])
        self.assertEqual(party_on_application.party.country, get_country(data["country"]))
        self.assertEqual(party_on_application.party.sub_type, data_type)
        self.assertEqual(party_on_application.party.sub_type_other, data.get("sub_type_other"))
        self.assertEqual(party_on_application.party.website, data["website"])

    def test_set_end_user_on_open_draft_application_success(self):
        data = {
            "name": "Lemonworld Org",
            "address": "3730 Martinsburg Rd, Gambier, Ohio",
            "signatory_name_euu": "Lemonworld",
            "country": "US",
            "sub_type": SubType.INDIVIDUAL,
            "type": PartyType.END_USER,
        }
        response = self.client.post(self.url, data, **self.exporter_headers)
        end_user = response.json()["end_user"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(end_user["name"], data["name"])
        self.assertEqual(end_user["address"], data["address"])
        self.assertEqual(end_user["signatory_name_euu"], data["signatory_name_euu"])
        self.assertEqual(end_user["country"]["id"], data["country"])
        self.assertEqual(end_user["sub_type"]["key"], data["sub_type"])

    @parameterized.expand(
        [
            [{}],
            [
                {
                    "name": "Lemonworld Org",
                    "address": "3730 Martinsburg Rd, Gambier, Ohio",
                    "country": "US",
                    "website": "https://www.americanmary.com",
                    "type": PartyType.END_USER,
                }
            ],
            [
                {
                    "name": "Lemonworld Org",
                    "address": "3730 Martinsburg Rd, Gambier, Ohio",
                    "country": "US",
                    "sub_type": "business",
                    "website": "https://www.americanmary.com",
                    "type": PartyType.END_USER,
                }
            ],
        ]
    )
    def test_set_end_user_on_non_draft_standard_application_failure(self, data):
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            PartyOnApplication.objects.filter(
                party__type=PartyType.END_USER,
                application=self.draft,
                deleted_at__isnull=True,
            ).count(),
            1,
        )

    @mock.patch("api.documents.models.Document.delete_s3")
    def test_end_user_is_deleted_when_new_one_added(self, delete_s3_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        When a new end user is added
        Then the old one is removed
        """
        party_on_application = PartyOnApplication.objects.get(
            application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True
        )

        self.client.post(self.url, self.new_end_user_data, **self.exporter_headers)
        try:
            party_on_application.refresh_from_db()
            self.fail(f"party_on_application not deleted: {party_on_application}")
        except PartyOnApplication.DoesNotExist:
            pass

        new_party_on_application = PartyOnApplication.objects.get(
            application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True
        )

        self.assertNotEqual(party_on_application.id, new_party_on_application.id)
        delete_s3_function.assert_not_called()

    def test_delete_end_user_on_standard_application_when_application_has_no_end_user_failure(
        self,
    ):
        """
        Given a draft standard application
        When I try to delete an end user from the application
        Then a 404 NOT FOUND is returned
        """
        party_on_application = PartyOnApplication.objects.get(
            application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True
        )

        party_on_application.delete()

        url = reverse("applications:party", kwargs={"pk": self.draft.id, "party_pk": party_on_application.party_id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now")
    def test_get_end_user_document_successful(self, scan_document_for_viruses_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached end user document
        """
        response = self.client.get(self.document_url, **self.exporter_headers)
        response_data = response.json()["document"]
        expected = self.new_document_data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["name"], "document_name.pdf")
        self.assertEqual(response_data["s3_key"], expected["s3_key"])
        self.assertEqual(response_data["size"], expected["size"])

    def test_get_document_when_no_end_user_exists_failure(self):
        """
        Given a standard draft has been created
        And the draft does not contain an end user
        When there is an attempt to retrieve a document
        Then a 400 BAD REQUEST is returned
        """
        PartyOnApplication.objects.get(
            application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True
        ).delete()

        response = self.client.get(self.document_url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now")
    def test_post_document_when_no_end_user_exists_failure(self, scan_document_for_viruses_function):
        """
        Given a standard draft has been created
        And the draft does not contain an end user
        When there is an attempt to submit a document
        Then a 400 BAD REQUEST is returned
        """
        PartyOnApplication.objects.get(
            application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True
        ).delete()

        response = self.client.post(self.document_url, data=self.new_document_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_document_when_no_end_user_exists_failure(self):
        """
        Given a standard draft has been created
        And the draft does not contain an end user
        When there is an attempt to delete a document
        Then a 400 BAD REQUEST is returned
        """
        PartyOnApplication.objects.filter(
            application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True
        ).delete()

        response = self.client.delete(self.document_url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_end_user_document_when_document_does_not_exist_failure(self):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user does not have a document attached
        When there is an attempt to get a document
        Then a 404 NOT FOUND is returned
        And the response contains a null document
        """
        party = PartyOnApplication.objects.get(
            application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True
        ).party
        PartyDocument.objects.filter(party=party).delete()

        response = self.client.get(self.document_url, **self.exporter_headers)

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual(None, response.json()["document"])

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now")
    def test_post_end_user_document_success(self, scan_document_for_viruses_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user does not have a document attached
        When a document is submitted
        Then a 201 CREATED is returned
        """
        party = PartyOnApplication.objects.get(
            application=self.draft, deleted_at__isnull=True, party__type=PartyType.END_USER
        ).party

        PartyDocument.objects.filter(party=party).delete()

        response = self.client.post(self.document_url, data=self.new_document_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now")
    def test_post_end_user_document_when_a_document_already_exists_success(self, scan_document_for_viruses_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When there is an attempt to post a document
        Then a 400 BAD REQUEST is returned
        """
        end_user = PartyOnApplication.objects.get(
            application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True
        ).party
        self.assertEqual(PartyDocument.objects.filter(party=end_user).count(), 1)

        response = self.client.post(self.document_url, data=self.new_document_data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        party_documents = PartyDocument.objects.filter(party=end_user)
        self.assertEqual(party_documents.count(), 1)
        self.assertEqual(party_documents.first().name, "updated_document_name.pdf")

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now")
    @mock.patch("api.documents.models.Document.delete_s3")
    def test_delete_end_user_document_success(self, delete_s3_function, scan_document_for_viruses_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When there is an attempt to delete the document
        Then 204 NO CONTENT is returned
        """
        response = self.client.delete(self.document_url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        delete_s3_function.assert_called_once()

    @mock.patch("api.documents.tasks.scan_document_for_viruses.now")
    @mock.patch("api.documents.models.Document.delete_s3")
    def test_delete_end_user_success(self, delete_s3_function, scan_document_for_viruses_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When there is an attempt to delete the end user
        Then 204 NO CONTENT is returned
        """
        end_user = PartyOnApplication.objects.get(
            application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True
        ).party
        url = reverse("applications:party", kwargs={"pk": self.draft.id, "party_pk": end_user.pk})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            PartyOnApplication.objects.filter(
                application=self.draft, deleted_at__isnull=False, party__type=PartyType.END_USER
            ).count(),
            0,
        )
        delete_s3_function.assert_not_called()

    def test_end_user_validate_only_success(self):
        """
        Given a standard draft has been created
        When there is an attempt to validate a end party's data
        Then 200 OK and end user is not created
        """
        end_user = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "signatory_name_euu": "UK Government",
            "country": "GB",
            "sub_type": "government",
            "website": "https://www.gov.uk",
            "validate_only": True,
            "type": PartyType.END_USER,
        }

        response = self.client.post(self.url, end_user, **self.exporter_headers)
        response_data = response.json()["end_user"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(self.draft.end_user.party.name, end_user["name"])
        self.assertEqual(response_data["name"], end_user["name"])
        self.assertEqual(response_data["signatory_name_euu"], end_user["signatory_name_euu"])
        self.assertEqual(response_data["address"], end_user["address"])
        self.assertEqual(response_data["country"], end_user["country"])
        self.assertEqual(response_data["sub_type"], end_user["sub_type"])
        self.assertEqual(response_data["website"], end_user["website"])

    def test_end_user_validate_only_failure(self):
        """
        Given a standard draft has been created
        When there is an attempt to validate an end user's data that is invalid (no name data)
        Then 400 Bad Request and end party is not created
        """
        end_user = {
            "address": "Westminster, London SW1A 0AA",
            "signatory_name_euu": "UK Government",
            "country": "GB",
            "sub_type": "government",
            "website": "https://www.gov.uk",
            "validate_only": True,
            "type": PartyType.END_USER,
        }

        response = self.client.post(self.url, end_user, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"name": [PartyErrors.NAME["null"]]}})

        end_user["name"] = "UK Government"
        end_user["signatory_name_euu"] = ""
        response = self.client.post(self.url, end_user, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"signatory_name_euu": ["Enter a name"]}})

    def test_end_user_copy_of_success(self):
        end_user = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "signatory_name_euu": "UK Government",
            "country": "GB",
            "sub_type": "government",
            "website": "https://www.gov.uk",
            "validate_only": False,
            "copy_of": self.draft.end_user.party.id,
            "type": PartyType.END_USER,
        }

        response = self.client.post(self.url, end_user, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["end_user"]["copy_of"], str(end_user["copy_of"]))


class EndUserOnNonDraftTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.app = self.create_standard_application_case(self.organisation)
        self.app.status = get_case_status_by_status("applicant_editing")
        self.app.save()
        self.app.refresh_from_db()

    def test_delete_end_user_on_standard_application_when_application_has_been_submitted(
        self,
    ):
        """
        Deletes the party_on_application instead of expiring
        """
        self.assertIsNotNone(self.app.end_user)
        party_on_application = self.app.end_user
        url = reverse("applications:party", kwargs={"pk": self.app.id, "party_pk": party_on_application.party_id})
        response = self.client.delete(url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            PartyOnApplication.objects.filter(
                application=self.app, party__type=PartyType.END_USER, deleted_at__isnull=True
            ).count(),
            0,
        )
