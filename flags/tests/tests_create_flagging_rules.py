from django.urls import reverse
from rest_framework import status

from applications.models import GoodOnApplication, PartyOnApplication
from cases.enums import CaseTypeReferenceEnum
from flags.models import FlaggingRule
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

        flag = self.create_flag("test", "Case", self.team)
        data = {"level": "Case", "flag": str(flag.id), "matching_value": CaseTypeReferenceEnum.SIEL}

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["level"], "Case")
        self.assertEqual(response_data["flag"], str(flag.id))
        self.assertEqual(response_data["matching_value"], CaseTypeReferenceEnum.SIEL)

        rule = FlaggingRule.objects.get()
        self.assertEqual(rule.level, "Case")
        self.assertEqual(rule.flag, flag)
        self.assertEqual(rule.matching_value, CaseTypeReferenceEnum.SIEL)

    def test_gov_user_can_create_flagging_rule_good(self):
        application = self.create_standard_application_case(self.organisation)
        control_list_entry = (
            GoodOnApplication.objects.filter(application_id=application.id)
            .values_list("good__control_list_entry", flat=True)
            .first()
        )

        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        flag = self.create_flag("test", "Good", self.team)
        data = {
            "level": "Good",
            "flag": str(flag.id),
            "matching_value": control_list_entry,
            "is_for_verified_goods_only": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["level"], "Good")
        self.assertEqual(response_data["flag"], str(flag.id))
        self.assertEqual(response_data["matching_value"], control_list_entry)
        self.assertTrue(response_data["is_for_verified_goods_only"])

        rule = FlaggingRule.objects.get()
        self.assertEqual(rule.level, "Good")
        self.assertEqual(rule.flag, flag)
        self.assertEqual(rule.matching_value, control_list_entry)

    def test_gov_user_can_create_flagging_rule_destination(self):
        application = self.create_standard_application_case(self.organisation)
        country_id = (
            PartyOnApplication.objects.filter(application_id=application)
            .values_list("party__country_id", flat=True)
            .first()
        )

        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        flag = self.create_flag("test", "Destination", self.team)
        data = {"level": "Destination", "flag": str(flag.id), "matching_value": country_id}

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["level"], "Destination")
        self.assertEqual(response_data["flag"], str(flag.id))
        self.assertEqual(response_data["matching_value"], country_id)

        rule = FlaggingRule.objects.get()
        self.assertEqual(rule.level, "Destination")
        self.assertEqual(rule.flag, flag)
        self.assertEqual(rule.matching_value, country_id)

    def test_create_flagging_rule_failure_duplicate(self):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        flag = self.create_flag("test", "Case", self.team)
        FlaggingRule(flag=flag, team=self.team, matching_value=CaseTypeReferenceEnum.SIEL, level="Case").save()

        response = self.client.post(
            self.url,
            {"level": "Case", "flag": str(flag.id), "matching_value": CaseTypeReferenceEnum.SIEL},
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

        flag = self.create_flag("test", "Good", self.team)
        data = {"level": "Good", "flag": str(flag.id), "matching_value": control_list_entry}

        response = self.client.post(self.url, data, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_data["errors"]["is_for_verified_goods_only"], [strings.FlaggingRules.NO_ANSWER_VERIFIED_ONLY]
        )
