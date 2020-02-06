from unittest import mock

from django.urls import reverse
from rest_framework import status

from applications.models import PartyOnApplication
from lite_content.lite_api.strings import Parties
from parties.enums import PartyType
from parties.models import Party
from parties.models import PartyDocument
from test_helpers.clients import DataTestClient


class UltimateEndUsersOnDraft(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_application_with_incorporated_good(self.organisation)
        self.url = reverse("applications:parties", kwargs={"pk": self.draft.id})

        self.document_url = reverse(
            "applications:party_document",
            kwargs={"pk": self.draft.id, "party_pk": self.draft.ultimate_end_users.first().party.id},
        )
        self.new_document_data = {
            "name": "document_name.pdf",
            "s3_key": "s3_keykey.pdf",
            "size": 123456,
        }

    def test_set_multiple_ultimate_end_users_on_draft_successful(self):
        PartyOnApplication.objects.filter(application=self.draft, party__type=PartyType.ULTIMATE_END_USER).delete()

        data = [
            {
                "name": "UK Government",
                "address": "Westminster, London SW1A 0AA",
                "country": "GB",
                "sub_type": "commercial",
                "website": "https://www.gov.uk",
                "type": PartyType.ULTIMATE_END_USER,
            },
            {
                "name": "French Government",
                "address": "Paris",
                "country": "FR",
                "sub_type": "government",
                "website": "https://www.gov.fr",
                "type": PartyType.ULTIMATE_END_USER,
            },
        ]

        for ultimate_end_user in data:
            self.client.post(self.url, ultimate_end_user, **self.exporter_headers)

        self.assertEqual(self.draft.ultimate_end_users.count(), 2)

    def test_unsuccessful_add_ultimate_end_user(self):
        data = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "website": "https://www.gov.uk",
            "type": PartyType.ULTIMATE_END_USER,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data, {"errors": {"sub_type": [Parties.NULL_TYPE]}})

    def test_get_ultimate_end_users(self):
        PartyOnApplication.objects.filter(application=self.draft, party__type=PartyType.ULTIMATE_END_USER).delete()

        ultimate_end_user = self.create_party(
            "ultimate end user", self.organisation, PartyType.ULTIMATE_END_USER, self.draft
        )

        response = self.client.get(f"{self.url}?type={PartyType.ULTIMATE_END_USER}", **self.exporter_headers)
        ultimate_end_users = response.json()["ultimate_end_users"]

        self.assertEqual(len(ultimate_end_users), 1)
        self.assertEqual(ultimate_end_users[0]["id"], str(ultimate_end_user.id))
        self.assertEqual(ultimate_end_users[0]["name"], str(ultimate_end_user.name))
        self.assertEqual(
            ultimate_end_users[0]["country"]["name"], str(ultimate_end_user.country.name),
        )
        self.assertEqual(ultimate_end_users[0]["website"], str(ultimate_end_user.website))
        self.assertEqual(ultimate_end_users[0]["type"], str(ultimate_end_user.type))
        self.assertEqual(
            ultimate_end_users[0]["organisation"], str(ultimate_end_user.organisation.id),
        )
        self.assertEqual(ultimate_end_users[0]["sub_type"]["key"], str(ultimate_end_user.sub_type))

    def test_set_ueu_on_draft_open_application_failure(self):
        """
        Given a draft open application
        When I try to add an ultimate end user to the application
        Then a 400 BAD REQUEST is returned
        And no ultimate end users have been added
        """
        pre_test_ueu_count = Party.objects.filter(type=PartyType.ULTIMATE_END_USER).count()
        data = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "commercial",
            "website": "https://www.gov.uk",
            "type": PartyType.ULTIMATE_END_USER,
        }

        open_draft = self.create_open_application(self.organisation)
        url = reverse("applications:parties", kwargs={"pk": open_draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Party.objects.filter(type=PartyType.ULTIMATE_END_USER).count(), pre_test_ueu_count)

    def test_delete_ueu_on_standard_application_when_application_has_no_ueu_failure(self,):
        """
        Given a draft standard application
        When I try to delete an ultimate end user from the application
        Then a 404 NOT FOUND is returned
        """
        ultimate_end_user = self.draft.ultimate_end_users.first().party
        PartyOnApplication.objects.filter(application=self.draft, party__type=PartyType.ULTIMATE_END_USER).delete()
        url = reverse("applications:parties", kwargs={"pk": self.draft.id, "party_pk": ultimate_end_user.id},)

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch("documents.tasks.prepare_document.now")
    def test_post_ultimate_end_user_document_success(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an ultimate end user
        And the ultimate end user does not have a document attached
        When a document is submitted
        Then a 201 CREATED is returned
        """
        PartyDocument.objects.filter(party=self.draft.ultimate_end_users.first().party).delete()

        response = self.client.post(self.document_url, data=self.new_document_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @mock.patch("documents.tasks.prepare_document.now")
    def test_get_ultimate_end_user_document_success(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an ultimate end user
        And the ultimate end user has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached ultimate end user document
        """
        response = self.client.get(self.document_url, **self.exporter_headers)
        response_data = response.json()["document"]
        expected = self.new_document_data

        self.assertEqual(response_data["name"], expected["name"])
        self.assertEqual(response_data["s3_key"], expected["s3_key"])
        self.assertEqual(response_data["size"], expected["size"])

    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_ultimate_end_user_document_success(self, delete_s3_function, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an ultimate end user
        And the draft contains an ultimate end user document
        When there is an attempt to delete the document
        Then 204 NO CONTENT is returned
        """
        response = self.client.delete(self.document_url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        delete_s3_function.assert_called_once()

    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_ultimate_end_user_success(self, delete_s3_function, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains an ultimate end user
        And the draft contains an ultimate end user document
        When there is an attempt to delete the document
        Then 200 OK
        """
        url = reverse(
            "applications:parties",
            kwargs={"pk": self.draft.id, "party_pk": self.draft.ultimate_end_users.first().party.id},
        )

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            PartyOnApplication.objects.filter(
                application=self.draft, party__type=PartyType.ULTIMATE_END_USER, deleted_at__isnull=False,
            ).count(),
            1,
        )
        delete_s3_function.assert_not_called()

    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_ultimate_end_user_success(self, delete_s3_function, prepare_document_function):
        self.assertEqual(self.draft.ultimate_end_users.count(), 1)

        url = reverse(
            "applications:parties",
            kwargs={"pk": self.draft.id, "party_pk": self.draft.ultimate_end_users.first().party.id},
        )

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.draft.ultimate_end_users.count(), 0)

    def test_ultimate_end_user_validate_only_success(self):
        """
        Given a standard draft has been created
        When there is an attempt to validate an ultimate end user's data
        Then 200 OK and ultimate end user is not created
        """
        ultimate_end_user = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "government",
            "role": "agent",
            "website": "https://www.gov.uk",
            "validate_only": True,
            "type": PartyType.ULTIMATE_END_USER,
        }

        original_party_count = self.draft.ultimate_end_users.count()
        self.draft.refresh_from_db()

        response = self.client.post(self.url, ultimate_end_user, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(original_party_count, self.draft.ultimate_end_users.count())

    def test_ultimate_end_user_validate_only_failure(self):
        """
        Given a standard draft has been created
        When there is an attempt to validate a ultimate_end_user's data that is invalid (no name data)
        Then 400 Bad Request and the ultimate_end_user is not created
        """
        ultimate_end_user = {
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "government",
            "website": "https://www.gov.uk",
            "validate_only": True,
            "type": PartyType.ULTIMATE_END_USER,
        }

        original_party_count = self.draft.ultimate_end_users.count()
        self.draft.refresh_from_db()

        response = self.client.post(self.url, ultimate_end_user, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(original_party_count, self.draft.ultimate_end_users.count())
        self.assertEqual(response.json(), {"errors": {"name": [Parties.REQUIRED_FIELD]}})

    def test_ultimate_end_user_copy_of_success(self):
        ultimate_end_user = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "government",
            "website": "https://www.gov.uk",
            "validate_only": False,
            "copy_of": self.draft.end_user.party.id,
            "type": PartyType.ULTIMATE_END_USER,
        }

        # Delete existing ultimate end user to enable easy assertion of copied ultimate end user
        delete_url = reverse(
            "applications:parties",
            kwargs={"pk": self.draft.id, "party_pk": self.draft.ultimate_end_users.first().party.id},
        )
        self.client.delete(delete_url, **self.exporter_headers)

        response = self.client.post(self.url, ultimate_end_user, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.draft.end_user.party.id, self.draft.ultimate_end_users.first().party.copy_of.id)
        self.assertEqual(response.json()["ultimate_end_user"]["copy_of"], str(ultimate_end_user["copy_of"]))
