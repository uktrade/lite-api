from unittest import mock

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from applications.libraries.case_status_helpers import get_case_statuses
from audit_trail.models import Audit
from parties.models import PartyDocument, Party
from parties.models import ThirdParty
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from lite_content.lite_api.strings import Parties


class ThirdPartiesOnDraft(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_application(self.organisation)
        self.url = reverse("applications:third_parties", kwargs={"pk": self.draft.id})

        self.document_url = reverse(
            "applications:third_party_document",
            kwargs={"pk": self.draft.id, "tp_pk": self.draft.third_parties.first().id},
        )
        self.new_document_data = {
            "name": "document_name.pdf",
            "s3_key": "s3_keykey.pdf",
            "size": 123456,
        }

    def test_set_multiple_third_parties_on_draft_successful(self):
        """
        Given a standard draft has been created
        And the draft does not yet contain a third party
        When multiple third parties are added
        Then all third parties are successfully added to the draft
        """
        audit_qs = Audit.objects.all()
        self.draft.third_parties.set([])
        parties = [
            {
                "name": "UK Government",
                "address": "Westminster, London SW1A 0AA",
                "country": "GB",
                "sub_type": "government",
                "role": "agent",
                "website": "https://www.gov.uk",
            },
            {
                "name": "French Government",
                "address": "Paris",
                "country": "FR",
                "sub_type": "government",
                "role": "other",
                "website": "https://www.gov.fr",
            },
        ]

        for count, third_party in enumerate(parties, 1):
            response = self.client.post(self.url, third_party, **self.exporter_headers)
            response_party = response.json()["third_party"]

            self.assertEqual(self.draft.third_parties.count(), count)
            self.assertEqual(third_party["name"], response_party["name"])
            self.assertEqual(third_party["address"], response_party["address"])
            self.assertEqual(third_party["country"], response_party["country"]["id"])
            self.assertEqual(third_party["sub_type"], response_party["sub_type"]["key"])
            self.assertEqual(third_party["role"], response_party["role"]["key"])
            self.assertEqual(third_party["website"], response_party["website"])

        # Drafts do not create audit
        self.assertEqual(audit_qs.count(), 0)
        self.assertEqual(self.draft.third_parties.count(), len(parties))

    @parameterized.expand(
        [
            [
                {},
                {
                    "errors": {
                        "name": [Parties.REQUIRED_FIELD],
                        "address": [Parties.REQUIRED_FIELD],
                        "country": [Parties.REQUIRED_FIELD],
                        "sub_type": [Parties.NULL_TYPE],
                        "role": [Parties.ThirdParty.NULL_ROLE],
                    }
                },
            ],
            [
                {
                    "name": "UK Government",
                    "address": "Westminster, London SW1A 0AA",
                    "country": "GB",
                    "website": "https://www.gov.uk",
                },
                {"errors": {"sub_type": [Parties.NULL_TYPE], "role": [Parties.ThirdParty.NULL_ROLE]}},
            ],
        ]
    )
    def test_unsuccessful_add_third_party(self, data, errors):
        """
        Given a standard draft has been created
        And the draft does not yet contain a third party
        When attempting to add an invalid third party
        Then the third party is not added to the draft
        """
        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data, errors)

    def test_get_third_parties(self):
        third_party = self.draft.third_parties.first()
        response = self.client.get(self.url, **self.exporter_headers)
        third_parties = response.json()["third_parties"]

        self.assertEqual(len(third_parties), 1)
        self.assertEqual(third_parties[0]["id"], str(third_party.id))
        self.assertEqual(third_parties[0]["name"], str(third_party.name))
        self.assertEqual(third_parties[0]["country"]["name"], str(third_party.country.name))
        self.assertEqual(third_parties[0]["website"], str(third_party.website))
        self.assertEqual(third_parties[0]["type"], str(third_party.type))
        self.assertEqual(third_parties[0]["organisation"], str(third_party.organisation.id))
        self.assertEqual(third_parties[0]["sub_type"]["key"], str(third_party.sub_type))
        self.assertEqual(third_parties[0]["role"]["key"], str(third_party.role))

    def test_set_third_parties_on_draft_open_application_failure(self):
        """
        Given a draft open application
        When I try to add a third party to the application
        Then a 400 BAD REQUEST is returned
        And no third parties have been added
        """
        pre_test_third_party_count = ThirdParty.objects.all().count()
        data = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "agent",
            "website": "https://www.gov.uk",
        }
        open_draft = self.create_open_application(self.organisation)
        url = reverse("applications:third_parties", kwargs={"pk": open_draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ThirdParty.objects.all().count(), pre_test_third_party_count)

        audit_qs = Audit.objects.all()

        self.assertEqual(audit_qs.count(), 0)

    def test_delete_third_party_on_standard_application_when_application_has_no_third_parties_failure(self,):
        """
        Given a draft standard application
        When I try to delete a third party from the application
        Then a 404 NOT FOUND is returned
        """
        third_party = self.draft.third_parties.first()
        self.draft.third_parties.set([])
        url = reverse("applications:remove_third_party", kwargs={"pk": self.draft.id, "tp_pk": third_party.id},)

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch("documents.tasks.prepare_document.now")
    def test_post_third_party_document_success(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a third party
        And the third party does not have a document attached
        When a document is submitted
        Then a 201 CREATED is returned
        """
        PartyDocument.objects.filter(party=self.draft.third_parties.first()).delete()

        response = self.client.post(self.document_url, data=self.new_document_data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @mock.patch("documents.tasks.prepare_document.now")
    def test_get_third_party_document_success(self, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a third party
        And the third party has a document attached
        When the document is retrieved
        Then the data in the document is the same as the data in the attached third party document
        """
        response = self.client.get(self.document_url, **self.exporter_headers)
        response_data = response.json()["document"]
        expected = self.new_document_data

        self.assertEqual(response_data["name"], expected["name"])
        self.assertEqual(response_data["s3_key"], expected["s3_key"])
        self.assertEqual(response_data["size"], expected["size"])

    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_third_party_document_success(self, delete_s3_function, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a third party
        And the draft contains a third party document
        When there is an attempt to delete the document
        Then 204 NO CONTENT is returned
        """
        response = self.client.delete(self.document_url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        delete_s3_function.assert_called_once()

    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_third_party_success(self, delete_s3_function, prepare_document_function):
        """
        Given a standard draft has been created
        And the draft contains a third party
        And the draft contains a third party document
        When there is an attempt to delete third party
        Then 200 OK
        """
        remove_tp_url = reverse(
            "applications:remove_third_party",
            kwargs={"pk": self.draft.id, "tp_pk": self.draft.third_parties.first().id},
        )

        response = self.client.delete(remove_tp_url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ThirdParty.objects.all().count(), 0)
        delete_s3_function.assert_called_once()

    @parameterized.expand(get_case_statuses(read_only=False))
    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_third_party_when_application_editable_success(
        self, editable_status, delete_s3_function, prepare_document_function
    ):
        application = self.create_standard_application(self.organisation)
        application.status = get_case_status_by_status(editable_status)
        application.save()
        url = reverse(
            "applications:remove_third_party",
            kwargs={"pk": application.id, "tp_pk": application.third_parties.first().id,},
        )

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(application.third_parties.count(), 0)

    @parameterized.expand(get_case_statuses(read_only=True))
    @mock.patch("documents.tasks.prepare_document.now")
    @mock.patch("documents.models.Document.delete_s3")
    def test_delete_third_party_when_application_read_only_failure(
        self, read_only_status, delete_s3_function, prepare_document_function
    ):
        application = self.create_standard_application(self.organisation)
        application.status = get_case_status_by_status(read_only_status)
        application.save()
        url = reverse(
            "applications:remove_third_party",
            kwargs={"pk": application.id, "tp_pk": application.third_parties.first().id},
        )

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(application.third_parties.count(), 1)

    def test_third_party_validate_only_success(self):
        """
        Given a standard draft has been created
        When there is an attempt to validate a third party's data
        Then 200 OK and third party is not created
        """
        third_party = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "government",
            "role": "agent",
            "website": "https://www.gov.uk",
            "validate_only": True,
        }

        original_party_count = self.draft.third_parties.count()

        response = self.client.post(self.url, third_party, **self.exporter_headers)
        response_data = response.json()['third_party']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(original_party_count, self.draft.third_parties.count())
        self.assertEqual(response_data['name'], third_party['name'])
        self.assertEqual(response_data['address'], third_party['address'])
        self.assertEqual(response_data['country'], third_party['country'])
        self.assertEqual(response_data['sub_type'], third_party['sub_type'])
        self.assertEqual(response_data['website'], third_party['website'])
        self.assertEqual(response_data['role'], third_party['role'])

    def test_third_party_validate_only_failure(self):
        """
        Given a standard draft has been created
        When there is an attempt to validate a third party's data that is invalid (no role data)
        Then 400 Bad Request and third party is not created
        """
        third_party = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "government",
            "website": "https://www.gov.uk",
            "validate_only": True,
        }

        original_party_count = self.draft.third_parties.count()

        response = self.client.post(self.url, third_party, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(original_party_count, self.draft.third_parties.count())
        self.assertEqual(response.json(), {"errors": {"role": [Parties.ThirdParty.NULL_ROLE]}})

    def test_third_party_copy_of_success(self):
        third_party = {
            "name": "UK Government",
            "address": "Westminster, London SW1A 0AA",
            "country": "GB",
            "sub_type": "government",
            "website": "https://www.gov.uk",
            "validate_only": False,
            "role": "agent",
            "copy_of": self.draft.end_user.id,
        }

        # Delete existing third party to enable easy assertion of copied third party
        delete_url = reverse(
            "applications:remove_third_party",
            kwargs={"pk": self.draft.id, "tp_pk": self.draft.third_parties.first().id},
        )
        self.client.delete(delete_url, **self.exporter_headers)

        response = self.client.post(self.url, third_party, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.draft.end_user.id, self.draft.third_parties.first().copy_of.id)
        self.assertEqual(response.json()["third_party"]["copy_of"], str(third_party["copy_of"]))
