from rest_framework import status
from rest_framework.reverse import reverse

from api.applications.enums import SecurityClassifiedApprovalsType
from api.applications.tests.factories import DraftStandardApplicationFactory
from api.parties.enums import PartyType
from api.parties.tests.factories import PartyDocumentFactory
from test_helpers.clients import DataTestClient


class ApplicationsSecurityApprovalsTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = DraftStandardApplicationFactory(organisation=self.organisation)
        end_user = self.draft.parties.filter(party__type=PartyType.END_USER).first()
        PartyDocumentFactory(party=end_user.party, s3_key="some secret key", safe=True)

        self.url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})

    def test_application_submit_with_security_approvals_success(self):
        self.draft.is_mod_security_approved = True
        self.draft.security_approvals = [SecurityClassifiedApprovalsType.F680]
        self.draft.subject_to_itar_controls = False
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = response.json()["application"]
        self.assertEqual(response["is_mod_security_approved"], True)
        self.assertEqual(response["security_approvals"], [SecurityClassifiedApprovalsType.F680])
        self.assertEqual(response["subject_to_itar_controls"], False)

    def test_application_submit_fail_without_security_approvals(self):
        self.draft.is_mod_security_approved = None
        self.draft.save()

        response = self.client.put(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = response.json()["errors"]
        self.assertEqual(
            response["security_approvals"],
            ["To submit the application, complete the 'Do you have a security approval?' section"],
        )

    def test_edit_itar_controls_status(self):
        self.draft.is_mod_security_approved = True
        self.draft.security_approvals = [SecurityClassifiedApprovalsType.OTHER]
        self.draft.subject_to_itar_controls = False
        self.draft.save()

        url = reverse("applications:application", kwargs={"pk": self.draft.id})
        data = {
            "security_approvals": [SecurityClassifiedApprovalsType.F680],
            "subject_to_itar_controls": True,
        }
        response = self.client.put(url, data=data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.draft.refresh_from_db()
        self.assertEqual(self.draft.is_mod_security_approved, True)
        self.assertEqual(self.draft.security_approvals, [SecurityClassifiedApprovalsType.F680])
        self.assertEqual(self.draft.subject_to_itar_controls, True)
