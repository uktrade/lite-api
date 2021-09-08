import pytest

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import AdviceType
from api.cases.models import Advice
from api.core.constants import GovPermissions
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class CreateCaseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.application)

        self.standard_case_url = reverse("cases:user_advice", kwargs={"pk": self.case.id})

    def test_create_advice_good(self):
        data = {
            "user": self.gov_user.baseuser_ptr.id,
            "good": str(self.application.goods.first().good.id),
            "text": "Text",
            "type": AdviceType.APPROVE,
            "level": "user",
            "team": self.team.id,
            "proviso": "",
            "denial_reasons": [],
            "note": "",
            "footnote": None,
            "footnote_required": "False",
            "case": self.case.id,
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(Advice.objects.get())
        self.assertTrue(Audit.objects.filter(verb=AuditType.CREATED_USER_ADVICE).exists())

    def test_create_advice_good_on_application(self):
        data = {
            "user": self.gov_user.baseuser_ptr.id,
            "good": str(self.application.goods.first().id),
            "text": "Text",
            "type": AdviceType.APPROVE,
            "level": "user",
            "team": self.team.id,
            "proviso": "",
            "denial_reasons": [],
            "note": "",
            "footnote": None,
            "footnote_required": "False",
            "case": self.case.id,
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(Advice.objects.get())
        self.assertTrue(Audit.objects.filter(verb=AuditType.CREATED_USER_ADVICE).exists())

    @parameterized.expand(
        [
            [AdviceType.APPROVE],
            [AdviceType.PROVISO],
            [AdviceType.REFUSE],
            [AdviceType.NO_LICENCE_REQUIRED],
            [AdviceType.NOT_APPLICABLE],
        ]
    )
    def test_create_end_user_case_advice(self, advice_type):
        """
        Tests that a gov user can create an approval/proviso/refuse/nlr/not_applicable
        piece of advice for an end user
        """
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": advice_type,
            "end_user": str(self.application.end_user.party.id),
        }

        if advice_type == AdviceType.PROVISO:
            data["proviso"] = "I am easy to proviso"

        if advice_type == AdviceType.REFUSE:
            data["denial_reasons"] = ["1a", "1b", "1c"]

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(Advice.objects.get())
        self.assertTrue(Audit.objects.filter(verb=AuditType.CREATED_USER_ADVICE).exists())

    @pytest.mark.xfail(reason="This test was set up incorrectly so never worked as intended")
    def test_cannot_create_advice_for_two_items(self):
        """
        Tests that a gov user cannot create a piece of advice for more than one item
        """
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            # this passes the GoodOnApplication id to the Advice model which is why we get a 400 here
            # NOT because the user is trying to create advice for two different items
            "good": str(self.application.goods.first().id),
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Advice.objects.count(), 0)

    @parameterized.expand(CaseStatusEnum.terminal_statuses())
    def test_cannot_create_advice_when_case_in_terminal_state(self, terminal_status):
        self.application.status = get_case_status_by_status(terminal_status)
        self.application.save()

        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            "good": str(self.application.goods.first().id),
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_add_footnote_without_permission(self):
        self.gov_user.role.permissions.remove(GovPermissions.MAINTAIN_FOOTNOTES.name)
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            "footnote_required": "True",
            "footnote": "footnote",
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        response_data = response.json()["advice"][0]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["footnote"], None)
        self.assertEqual(Advice.objects.filter(footnote_required=None, footnote=None).count(), 1)

    def test_cannot_create_advice_without_footnote_and_having_permission(self):
        self.gov_user.role.permissions.add(GovPermissions.MAINTAIN_FOOTNOTES.name)
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_create_advice_with_footnote_not_required(self):
        self.gov_user.role.permissions.add(GovPermissions.MAINTAIN_FOOTNOTES.name)
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            "footnote_required": "False",
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        response_data = response.json()["advice"][0]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["footnote"], None)
        self.assertEqual(Advice.objects.filter(footnote_required=False, footnote=None).count(), 1)

    def test_cannot_create_advice_with_footnote_required_and_no_footnote(self):
        self.gov_user.role.permissions.add(GovPermissions.MAINTAIN_FOOTNOTES.name)
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            "footnote_required": "True",
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_create_advice_with_footnote_required(self):
        self.gov_user.role.permissions.add(GovPermissions.MAINTAIN_FOOTNOTES.name)
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.party.id),
            "footnote_required": "True",
            "footnote": "footnote",
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        response_data = response.json()["advice"][0]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["footnote"], "footnote")
        self.assertEqual(Advice.objects.filter(footnote_required=True, footnote=data["footnote"]).count(), 1)
