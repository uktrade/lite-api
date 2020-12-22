from django.urls import reverse
from rest_framework import status

from api.applications.models import GoodOnApplication, PartyOnApplication
from api.cases.enums import CaseTypeReferenceEnum
from api.flags.enums import FlagLevels
from api.flags.models import FlaggingRule
from api.flags.tests.factories import FlagFactory
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient


class FlaggingRulesCreateTest(DataTestClient):
    url = reverse("flags:flagging_rules")

    def test_gov_user_can_create_flagging_rule_case(self):
        self.create_standard_application_case(self.organisation)
        open_application = self.create_draft_open_application(self.organisation)
        self.submit_application(open_application)

        self.create_draft_open_application(self.organisation)
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        flag = FlagFactory(level=FlagLevels.CASE, team=self.team)
        data = {
            "level": FlagLevels.CASE,
            "flag": str(flag.id),
            "matching_values": [CaseTypeReferenceEnum.SIEL, CaseTypeReferenceEnum.OGEL],
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["level"], FlagLevels.CASE)
        self.assertEqual(response_data["flag"], str(flag.id))
        self.assertEqual(response_data["matching_values"], [CaseTypeReferenceEnum.SIEL, CaseTypeReferenceEnum.OGEL])

        rule = FlaggingRule.objects.get()
        self.assertEqual(rule.level, "Case")
        self.assertEqual(rule.flag, flag)
        self.assertEqual(rule.matching_values, [CaseTypeReferenceEnum.SIEL, CaseTypeReferenceEnum.OGEL])

    def test_gov_user_can_create_flagging_rule_good(self):
        application = self.create_standard_application_case(self.organisation)
        goa = GoodOnApplication.objects.filter(application_id=application.id).first()
        clc1 = goa.good.control_list_entries.first()
        clc2 = goa.good.control_list_entries.last()

        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        flag = FlagFactory(level=FlagLevels.GOOD, team=self.team)
        data = {
            "level": FlagLevels.GOOD,
            "flag": str(flag.id),
            "matching_values": [clc1.rating, clc2.rating],
            "is_for_verified_goods_only": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["level"], FlagLevels.GOOD)
        self.assertEqual(response_data["flag"], str(flag.id))
        self.assertEqual(response_data["matching_values"], [clc1.rating, clc2.rating])
        self.assertTrue(response_data["is_for_verified_goods_only"])

        rule = FlaggingRule.objects.get()
        self.assertEqual(rule.level, FlagLevels.GOOD)
        self.assertEqual(rule.flag, flag)
        self.assertEqual(rule.matching_values, [clc1.rating, clc2.rating])

    def test_gov_user_can_create_flagging_rule_destination(self):
        application = self.create_standard_application_case(self.organisation)
        country_id = (
            PartyOnApplication.objects.filter(application_id=application)
            .values_list("party__country_id", flat=True)
            .first()
        )

        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        flag = FlagFactory(level=FlagLevels.DESTINATION, team=self.team)
        data = {"level": FlagLevels.DESTINATION, "flag": str(flag.id), "matching_values": [country_id]}

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["level"], FlagLevels.DESTINATION)
        self.assertEqual(response_data["flag"], str(flag.id))
        self.assertEqual(response_data["matching_values"], [country_id])

        rule = FlaggingRule.objects.get()
        self.assertEqual(rule.level, "Destination")
        self.assertEqual(rule.flag, flag)
        self.assertEqual(rule.matching_values, [country_id])

    def test_create_flagging_rule_failure_duplicate(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = FlagFactory(level=FlagLevels.CASE, team=self.team)
        FlaggingRule(flag=flag, team=self.team, matching_values=[CaseTypeReferenceEnum.SIEL], level="Case").save()

        response = self.client.post(
            self.url,
            {"level": FlagLevels.CASE, "flag": str(flag.id), "matching_values": [CaseTypeReferenceEnum.SIEL]},
            **self.gov_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(strings.FlaggingRules.DUPLICATE_RULE, response.json()["errors"]["non_field_errors"])

    def test_missing_data_create_good_rule_failure(self):
        application = self.create_standard_application_case(self.organisation)
        control_list_entry = (
            GoodOnApplication.objects.filter(application_id=application.id)
            .values_list("good__control_list_entries__rating", flat=True)
            .first()
        )

        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        flag = FlagFactory(level=FlagLevels.GOOD, team=self.team)
        data = {"level": FlagLevels.GOOD, "flag": str(flag.id), "matching_values": [control_list_entry]}

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data["errors"]["is_for_verified_goods_only"], [strings.FlaggingRules.NO_ANSWER_VERIFIED_ONLY]
        )
