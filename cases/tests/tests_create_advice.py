from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.enums import AdviceType
from cases.models import Advice
from conf.helpers import convert_queryset_to_str
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class CreateCaseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application(self.organisation)
        self.submit_application(self.application)
        self.standard_case = self.application.case.get()

        self.standard_case_url = reverse("cases:case_advice", kwargs={"pk": self.standard_case.id})

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
            "end_user": str(self.application.end_user.id),
        }

        if advice_type == AdviceType.PROVISO:
            data["proviso"] = "I am easy to proviso"

        if advice_type == AdviceType.REFUSE:
            data["denial_reasons"] = ["1a", "1b", "1c"]

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])
        response_data = response.json()["advice"][0]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response_data["text"], data["text"])
        self.assertEqual(response_data["note"], data["note"])
        self.assertEqual(response_data["type"]["key"], data["type"])
        self.assertEqual(response_data["end_user"], data["end_user"])

        advice_object = Advice.objects.get()

        # Ensure that proviso details aren't added unless the type sent is PROVISO
        if advice_type != AdviceType.PROVISO:
            self.assertTrue("proviso" not in response_data)
            self.assertEqual(advice_object.proviso, None)
        else:
            self.assertEqual(response_data["proviso"], data["proviso"])
            self.assertEqual(advice_object.proviso, data["proviso"])

        # Ensure that refusal details aren't added unless the type sent is REFUSE
        if advice_type != AdviceType.REFUSE:
            self.assertTrue("denial_reasons" not in response_data)
            self.assertEqual(advice_object.denial_reasons.count(), 0)
        else:
            self.assertCountEqual(data["denial_reasons"], response_data["denial_reasons"])
            self.assertCountEqual(
                convert_queryset_to_str(advice_object.denial_reasons.values_list("id", flat=True)),
                data["denial_reasons"],
            )

    def test_cannot_create_empty_advice(self):
        """
        Tests that a gov user cannot create an empty piece of advice for an end user
        """
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_advice_for_two_items(self):
        """
        Tests that a gov user cannot create a piece of advice for more than one item
        """
        data = {
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "type": AdviceType.APPROVE,
            "end_user": str(self.application.end_user.id),
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
            "end_user": str(self.application.end_user.id),
            "good": str(self.application.goods.first().id),
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
