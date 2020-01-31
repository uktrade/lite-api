from unittest import mock

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from applications.models import PartyOnApplication
from parties.enums import PartyType
from parties.models import PartyDocument
from parties.models import Party
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class EndUserOnDraftTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_application(self.organisation)
        self.url = reverse("applications:end_user", kwargs={"pk": self.draft.id})
        self.new_end_user_data = {
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "type": PartyType.END_USER
        }

        self.document_url = reverse("applications:end_user_document", kwargs={"pk": self.draft.id})
        self.new_document_data = {
            "name": "document_name.pdf",
            "s3_key": "s3_keykey.pdf",
            "size": 123456,
        }

    @parameterized.expand(["government", "commercial", "other"])
    def test_set_end_user_on_draft_standard_application_successful(self, data_type):
        data = {
            "name": "Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": data_type,
            "website": "https://www.gov.uk",
            "type": PartyType.END_USER,
        }

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
        self.assertEqual(party_on_application.party.country, get_country(data["country"]))
        self.assertEqual(party_on_application.party.sub_type, data_type)
        self.assertEqual(party_on_application.party.website, data["website"])

    def test_set_end_user_on_draft_open_application_failure(self):
        """
        Given a draft open application
        When I try to add an end user to the application
        Then a 404 NOT FOUND is returned
        And no end users have been added
        """
        pre_test_end_user_count = PartyOnApplication.objects.filter(application=self.draft, deleted_at__isnull=True, party__type=PartyType.END_USER).count()
        draft_open_application = self.create_open_application(organisation=self.organisation)
        data = {
            "name": "Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "government",
            "website": "https://www.gov.uk",
            "type": PartyType.END_USER,
        }
        url = reverse("applications:end_user", kwargs={"pk": draft_open_application.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Party.objects.filter(type=PartyType.END_USER).count(), pre_test_end_user_count)

    @parameterized.expand(
        [
            [{}],
            [
                {
                    "name": "Lemonworld Org",
                    "address": "3730 Martinsburg Rd, Gambier, Ohio",
                    "country": "US",
                    "website": "https://www.americanmary.com",
                    "type": PartyType.END_USER
                }
            ],
            [
                {
                    "name": "Lemonworld Org",
                    "address": "3730 Martinsburg Rd, Gambier, Ohio",
                    "country": "US",
                    "sub_type": "business",
                    "website": "https://www.americanmary.com",
                    "type": PartyType.END_USER
                }
            ],
        ]
    )
    def test_set_end_user_on_draft_standard_application_failure(self, data):
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            PartyOnApplication.objects.filter(
                party__type=PartyType.END_USER,
                application=self.draft,
                deleted_at__isnull=True,
            ).count(),
            1
        )

    @mock.patch("documents.models.Document.delete_s3")
    def test_end_user_is_deleted_when_new_one_added(self, delete_s3_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        When a new end user is added
        Then the old one is removed
        """
        poa = PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True)

        self.client.post(self.url, self.new_end_user_data, **self.exporter_headers)
        poa.refresh_from_db()

        new_poa = PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True)

        self.assertNotEqual(poa.id, new_poa.id)
        #delete_s3_function.assert_called_once()

    def test_set_end_user_on_open_draft_application_failure(self):
        """
        Given a draft open application
        When I try to add an end user to the application
        Then a 400 BAD REQUEST is returned
        And no end user has been added
        """
        data = {
            "name": "Government of Paraguay",
            "address": "Asuncion",
            "country": "PY",
            "sub_type": "government",
            "website": "https://www.gov.py",
            "type": PartyType.END_USER
        }

        open_draft = self.create_open_application(self.organisation)
        url = reverse("applications:end_user", kwargs={"pk": open_draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            PartyOnApplication.objects.filter(
                party__type=PartyType.END_USER,
                application=open_draft,
                deleted_at__isnull=True,
            ).count(),
            0
        )

    def test_delete_end_user_on_standard_application_when_application_has_no_end_user_failure(self,):
        """
        Given a draft standard application
        When I try to delete an end user from the application
        Then a 404 NOT FOUND is returned
        """
        poa = PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True)

        poa.delete()

        url = reverse("applications:remove_consignee", kwargs={"pk": self.draft.id, "party_pk": poa.party.pk})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch("documents.tasks.prepare_document.now")
    def test_get_end_user_document_successful(self, prepare_document_function):
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
        self.assertEqual(response_data["name"], expected["name"])
        self.assertEqual(response_data["s3_key"], expected["s3_key"])
        self.assertEqual(response_data["size"], expected["size"])

    def test_get_document_when_no_end_user_exists_failure(self):
        """
        Given a standard draft has been created
        And the draft does not contain an end user
        When there is an attempt to retrieve a document
        Then a 400 BAD REQUEST is returned
        """
        PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True).delete()

        response = self.client.get(self.document_url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch("documents.tasks.prepare_document.now")
    def test_post_document_when_no_end_user_exists_failure(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft does not contain an end user
        When there is an attempt to submit a document
        Then a 400 BAD REQUEST is returned
        """
        PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True).delete()

        response = self.client.post(self.document_url, data=self.new_document_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_document_when_no_end_user_exists_failure(self):
        """
        Given a standard draft has been created
        And the draft does not contain an end user
        When there is an attempt to delete a document
        Then a 400 BAD REQUEST is returned
        """
        PartyOnApplication.objects.filter(application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True).delete()

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
        party = PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True).party
        PartyDocument.objects.filter(party=party).delete()

        response = self.client.get(self.document_url, **self.exporter_headers)

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual(None, response.json()["document"])

    @mock.patch("documents.tasks.prepare_document.now")
    def test_post_end_user_document_success(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the end user does not have a document attached
        When a document is submitted
        Then a 201 CREATED is returned
        """
        party = PartyOnApplication.objects.get(
            application=self.draft,
            deleted_at__isnull=True,
            party__type=PartyType.END_USER
        ).party

        PartyDocument.objects.filter(party=party).delete()

        response = self.client.post(self.document_url, data=self.new_document_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @mock.patch("documents.tasks.prepare_document.now")
    def test_post_end_user_document_when_a_document_already_exists_failure(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When there is an attempt to post a document
        Then a 400 BAD REQUEST is returned
        """
        response = self.client.post(self.document_url, data=self.new_document_data, **self.exporter_headers)
        end_user = PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True).party

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PartyDocument.objects.filter(party=end_user).count(), 1)

    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_end_user_document_success(self, delete_s3_function, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When there is an attempt to delete the document
        Then 204 NO CONTENT is returned
        """
        response = self.client.delete(self.document_url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        #delete_s3_function.assert_called_once()

    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_end_user_success(self, delete_s3_function, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an end user
        And the draft contains an end user document
        When there is an attempt to delete the end user
        Then 204 NO CONTENT is returned
        """
        end_user = PartyOnApplication.objects.get(application=self.draft, party__type=PartyType.END_USER, deleted_at__isnull=True).party
        url = reverse("applications:remove_consignee", kwargs={"pk": self.draft.id, "party_pk": end_user.pk})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            PartyOnApplication.objects.filter(
                application=self.draft,
                deleted_at__isnull=False,
                party__type=PartyType.END_USER
            ).count(),
            1
        )
        #delete_s3_function.assert_called_once()
