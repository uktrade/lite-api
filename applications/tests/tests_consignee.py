from unittest import mock

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from applications.models import PartyOnApplication
from lite_content.lite_api.strings import Parties
from parties.enums import PartyType
from parties.models import PartyDocument
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class ConsigneeOnDraftTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_application(self.organisation)
        self.url = reverse("applications:consignee", kwargs={"pk": self.draft.id})
        self.document_url = reverse("applications:consignee_document", kwargs={"pk": self.draft.id})
        self.new_document_data = {
            "name": "document_name.pdf",
            "s3_key": "s3_keykey.pdf",
            "size": 123456,
        }

    @parameterized.expand(["government", "commercial", "other"])
    def test_set_consignee_on_draft_successful(self, data_type):
        """
        Given a standard draft has been created
        And the draft does not yet contain a consignee
        When a new consignee is added
        Then the consignee is successfully added to the draft
        """
        data = {
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": data_type,
            "website": "https://www.gov.py",
            "type": PartyType.CONSIGNEE
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        party_on_application = PartyOnApplication.objects.get(
            application=self.draft,
            party__type=PartyType.CONSIGNEE,
            deleted_at__isnull=True,
        )

        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(party_on_application.party.name, data["name"])
        self.assertEqual(party_on_application.party.address, data["address"])
        self.assertEqual(party_on_application.party.country, get_country(data["country"]))
        self.assertEqual(party_on_application.party.sub_type, data_type)
        self.assertEqual(party_on_application.party.website, data["website"])

    @parameterized.expand(
        [
            [{}],
            [
                {
                    "name": "Lemonworld Org",
                    "address": "3730 Martinsburg Rd, Gambier, Ohio",
                    "country": "US",
                    "website": "https://www.americanmary.com",
                    "type": PartyType.CONSIGNEE
                }
            ],
            [
                {
                    "name": "Lemonworld Org",
                    "address": "3730 Martinsburg Rd, Gambier, Ohio",
                    "country": "US",
                    "sub_type": "made-up",
                    "website": "https://www.americanmary.com",
                    "type": PartyType.CONSIGNEE
                }
            ],
        ]
    )
    def test_set_consignee_on_draft_failure(self, data):
        """
        Given a standard draft has been created
        And the draft does not yet contain a consignee
        When attempting to add an invalid consignee
        Then the consignee is not added to the draft
        """
        PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.CONSIGNEE).delete()

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.draft.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.draft.consignee, None)

    @mock.patch("documents.models.Document.delete_s3")
    def test_consignee_deleted_when_new_one_added(self, delete_s3_function):
        """
        Given a standard draft has been created
        And the draft contains a consignee
        When a new consignee is added
        Then the old one is removed
        """
        old_consignee = PartyOnApplication.objects.get(application=self.draft, deleted_at__isnull=True, party__type=PartyType.CONSIGNEE).party
        new_consignee = {
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "type": PartyType.CONSIGNEE
        }

        self.client.post(self.url, new_consignee, **self.exporter_headers)
        self.draft.refresh_from_db()

        deleted_consignees = PartyOnApplication.objects.filter(party=old_consignee, deleted_at__isnull=False)

        self.assertEqual(deleted_consignees.count(), 1)
        #delete_s3_function.assert_called_once()

    def test_set_consignee_on_open_draft_application_failure(self):
        """
        Given a draft open application
        When I try to add a consignee to the application
        Then a 400 BAD REQUEST is returned
        And no consignees have been added
        """
        PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.CONSIGNEE).delete()
        data = {
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "type": PartyType.CONSIGNEE
        }

        open_draft = self.create_open_application(self.organisation)
        url = reverse("applications:consignee", kwargs={"pk": open_draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            PartyOnApplication.objects.filter(
                application=self.draft,
                party__type=PartyType.CONSIGNEE,
                deleted_at__isnull=True
            ).count(),
            0
        )

    def test_delete_consignee_on_standard_application_when_application_has_no_consignee_failure(self,):
        """
        Given a draft standard application
        When I try to delete an consignee from the application
        Then a 404 NOT FOUND is returned
        """
        poa = PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.CONSIGNEE)
        poa.delete()

        url = reverse("applications:remove_consignee", kwargs={"pk": self.draft.id, "party_pk": poa.party.pk})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch("documents.tasks.prepare_document.now")
    def test_post_consignee_document_success(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a consignee
        And the consignee does not have a document attached
        When a document is submitted
        Then a 201 CREATED is returned
        """
        party = PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.CONSIGNEE, deleted_at__isnull=True).party
        PartyDocument.objects.filter(party=party).delete()

        response = self.client.post(self.document_url, data=self.new_document_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @mock.patch("documents.tasks.prepare_document.now")
    def test_get_consignee_document_success(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a consignee
        And the consignee has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached consignee document
        """
        response = self.client.get(self.document_url, **self.exporter_headers)
        response_data = response.json()["document"]
        expected = self.new_document_data

        self.assertEqual(response_data["name"], expected["name"])
        self.assertEqual(response_data["s3_key"], expected["s3_key"])
        self.assertEqual(response_data["size"], expected["size"])

    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_consignee_document_success(self, delete_s3_function, prepare_document_function):
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

    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_consignee_success(self, delete_s3_function, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a consignee user
        And the draft contains a consignee document
        When there is an attempt to delete the consignee
        Then 204 NO CONTENT is returned
        """
        consignee = PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.CONSIGNEE, deleted_at__isnull=True).party
        url = reverse("applications:remove_consignee", kwargs={"pk": self.draft.id, "party_pk": consignee.pk})
        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            PartyOnApplication.objects.filter(
                application=self.draft,
                party__type=PartyType.CONSIGNEE,
                deleted_at__isnull=False
            ).count(),
            1
        )
        #delete_s3_function.assert_called_once()

    def test_consignee_validate_only_success(self):
        """
        Given a standard draft has been created
        When there is an attempt to validate a consignee's data
        Then 200 OK and consignee is not created
        """
        consignee = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "government",
            "website": "https://www.gov.uk",
            "validate_only": True,
        }

        response = self.client.post(self.url, consignee, **self.exporter_headers)
        response_data = response.json()["consignee"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(self.draft.end_user.name, consignee["name"])
        self.assertEqual(response_data["name"], consignee["name"])
        self.assertEqual(response_data["address"], consignee["address"])
        self.assertEqual(response_data["country"], consignee["country"])
        self.assertEqual(response_data["sub_type"], consignee["sub_type"])
        self.assertEqual(response_data["website"], consignee["website"])

    def test_consignee_validate_only_failure(self):
        """
        Given a standard draft has been created
        When there is an attempt to validate an consignee's data that is invalid (no name data)
        Then 400 Bad Request and consignee is not created
        """
        end_user = {
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "government",
            "website": "https://www.gov.uk",
            "validate_only": True,
        }

        response = self.client.post(self.url, end_user, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"name": [Parties.REQUIRED_FIELD]}})

    def test_consignee_copy_of_success(self):
        consignee = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "government",
            "website": "https://www.gov.uk",
            "validate_only": False,
            "copy_of": self.draft.end_user.id,
        }

        response = self.client.post(self.url, consignee, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["consignee"]["copy_of"], str(consignee["copy_of"]))
