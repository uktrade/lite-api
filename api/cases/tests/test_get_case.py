from datetime import timedelta
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import Case
from lite_routing.routing_rules_internal.enums import FlagsEnum
from parameterized import parameterized
from rest_framework import status

from api.applications.models import CountryOnApplication
from api.cases.enums import CaseTypeEnum
from api.cases.tests.factories import CaseAssignmentFactory, FinalAdviceFactory, CountersignAdviceFactory
from api.flags.enums import SystemFlags
from api.flags.models import Flag
from api.flags.tests.factories import FlagFactory
from api.parties.enums import PartyType
from api.staticdata.countries.helpers import get_country
from api.staticdata.trade_control.enums import TradeControlActivity, TradeControlProductCategory
from test_helpers.clients import DataTestClient


class CaseGetTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)

    def test_case_returns_expected_third_party(self):
        """
        Given a case with a third party exists
        When the case is retrieved
        Then the third party is present in the json data
        """
        case = self.submit_application(self.standard_application)
        url = reverse("cases:case", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._assert_party(
            self.standard_application.third_parties.last().party,
            response_data["case"]["data"]["third_parties"][0],
        )
        self._assert_party(self.standard_application.consignee.party, response_data["case"]["data"]["consignee"])

    def _assert_party(self, expected, actual):
        self.assertEqual(str(expected.id), actual["id"])
        self.assertEqual(str(expected.name), actual["name"])
        self.assertEqual(str(expected.country.name), actual["country"]["name"])
        self.assertEqual(str(expected.website), actual["website"])
        self.assertEqual(str(expected.type), actual["type"])
        self.assertEqual(str(expected.organisation.id), actual["organisation"])

        sub_type = actual["sub_type"]
        # sub_type is not always a dict.
        self.assertEqual(
            str(expected.sub_type),
            sub_type["key"] if isinstance(sub_type, dict) else sub_type,
        )

    def test_case_returns_expected_goods_flags(self):
        case = self.submit_application(self.standard_application)
        url = reverse("cases:case", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_flags = [Flag.objects.get(id=SystemFlags.GOOD_NOT_YET_VERIFIED_ID).name, "Small Arms"]
        actual_flags_on_case = [flag["name"] for flag in response_data["case"]["all_flags"]]
        actual_flags_on_goods = [flag["name"] for flag in response_data["case"]["data"]["goods"][0]["flags"]]

        self.assertIn(actual_flags_on_case[0], expected_flags)
        for expected_flag in expected_flags:
            self.assertIn(expected_flag, actual_flags_on_goods)

    def test_case_assignments(self):
        case = self.submit_application(self.standard_application)
        assignment = CaseAssignmentFactory(case=case)
        url = reverse("cases:case", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_assignments = {
            assignment.queue.name: [
                {
                    "id": str(assignment.user.pk),
                    "first_name": assignment.user.first_name,
                    "last_name": assignment.user.last_name,
                    "email": assignment.user.email,
                    "assignment_id": str(assignment.id),
                }
            ]
        }
        assert response_data["case"]["assigned_users"] == expected_assignments

    def test_case_returns_expected_goods_types_flags(self):
        self.open_application = self.create_draft_open_application(self.organisation)
        self.open_case = self.submit_application(self.open_application)
        self.open_case_url = reverse("cases:case", kwargs={"pk": self.open_case.id})

        response = self.client.get(self.open_case_url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_flags = [
            Flag.objects.get(id=SystemFlags.GOOD_NOT_YET_VERIFIED_ID).name,
            "Small Arms",
            "UK Military/Para: Sch 2",
        ]
        actual_flags_on_case = [flag["name"] for flag in response_data["case"]["all_flags"]]
        actual_flags_on_goods_type = [flag["name"] for flag in response_data["case"]["data"]["goods_types"][0]["flags"]]

        self.assertIn(actual_flags_on_case[0], expected_flags)
        for expected_flag in expected_flags:
            self.assertIn(expected_flag, actual_flags_on_goods_type)

    def test_case_return_has_advice(self):
        case = self.submit_application(self.standard_application)
        url = reverse("cases:case", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj_type = ContentType.objects.get_for_model(Case)
        activity = Audit.objects.get(
            verb=AuditType.UPDATED_STATUS,
            target_object_id=case.id,
            target_content_type=obj_type,
        )
        self.assertEqual(str(activity.id), response.json()["case"]["latest_activity"]["id"])

        activity.delete()
        response = self.client.get(url, **self.gov_headers)
        assert response.json()["case"]["latest_activity"] == None

        activity = Audit.objects.create(
            actor=self.gov_user,
            verb=AuditType.ADD_CASE_OFFICER_TO_CASE,
            target_object_id=case.id,
            target_content_type=ContentType.objects.get_for_model(Case),
            payload={"case_officer": self.gov_user.email},
            created_at=timezone.now() - timedelta(days=2),
        )
        response = self.client.get(url, **self.gov_headers)
        self.assertEqual(str(activity.id), response.json()["case"]["latest_activity"]["id"])

        activity = Audit.objects.create(
            actor=self.system_user,
            verb=AuditType.ADDED_FLAG_ON_ORGANISATION,
            action_object_object_id=case.id,
            action_object_content_type=ContentType.objects.get_for_model(Case),
            payload={"flag_name": FlagsEnum.AG_CHEMICAL, "additional_text": "additional note here"},
            created_at=timezone.now() - timedelta(days=1),
        )
        response = self.client.get(url, **self.gov_headers)
        self.assertEqual(str(activity.id), response.json()["case"]["latest_activity"]["id"])

    def test_case_detail_custom_fields(self):
        case = self.submit_application(self.standard_application)
        second_queue = self.create_queue("Another Queue", self.team)
        case.queues.set([self.queue, second_queue])

        case.submitted_at = timezone.now() - timedelta(days=2)
        case.save()
        url = reverse("cases:case", kwargs={"pk": case.id})
        response = self.client.get(url, **self.gov_headers)
        data = response.json()["case"]

        self.assertEqual(2, data["total_days_elapsed"])
        self.assertEqual(str(second_queue.id), data["queue_details"][0]["id"])
        self.assertEqual(0, data["queue_details"][0]["days_on_queue_elapsed"])
        self.assertEqual(str(self.queue.id), data["queue_details"][1]["id"])
        self.assertEqual(0, data["queue_details"][1]["days_on_queue_elapsed"])

    def test_case_returns_has_activity(self):
        case = self.submit_application(self.standard_application)
        url = reverse("cases:case", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        has_advice_response_data = response.json()["case"]["has_advice"]
        self.assertIn("user", has_advice_response_data)
        self.assertIn("my_user", has_advice_response_data)
        self.assertIn("team", has_advice_response_data)
        self.assertIn("my_team", has_advice_response_data)
        self.assertIn("final", has_advice_response_data)

    def test_case_returns_countersign_advice(self):
        case = self.submit_application(self.standard_application)
        url = reverse("cases:case", kwargs={"pk": case.id})
        advice = FinalAdviceFactory(case=case, user=self.gov_user)
        countersign_advice = CountersignAdviceFactory(case=case, advice=advice)

        response = self.client.get(url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        response = response["case"]["countersign_advice"]
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["order"], countersign_advice.order)
        self.assertEqual(response[0]["outcome_accepted"], countersign_advice.outcome_accepted)
        self.assertEqual(response[0]["reasons"], countersign_advice.reasons)

    @parameterized.expand(
        [
            (CaseTypeEnum.SICL.id, DataTestClient.create_draft_standard_application),
            (CaseTypeEnum.OICL.id, DataTestClient.create_draft_open_application),
        ]
    )
    def test_trade_control_case(self, case_type_id, create_function):
        application = create_function(self, self.organisation, case_type_id=case_type_id)
        application.trade_control_activity = TradeControlActivity.OTHER
        application.trade_control_activity_other = "other activity"
        application.trade_control_product_categories = [key for key, _ in TradeControlProductCategory.choices]
        case = self.submit_application(application)

        url = reverse("cases:case", kwargs={"pk": case.id})
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case_application = response.json()["case"]["data"]

        trade_control_activity = case_application["trade_control_activity"]["value"]
        self.assertEqual(trade_control_activity, case.trade_control_activity_other)

        trade_control_product_categories = [
            category["key"] for category in case_application["trade_control_product_categories"]
        ]
        self.assertEqual(trade_control_product_categories, case.trade_control_product_categories)

    def test_countries_ordered_as_expected_on_open_application(self):
        highest_priority_flag = FlagFactory(
            name="highest priority flag", level="Destination", team=self.gov_user.team, priority=0
        )
        lowest_priority_flag = FlagFactory(
            name="lowest priority flag", level="Destination", team=self.gov_user.team, priority=10
        )

        open_application = self.create_draft_open_application(self.organisation)

        # Countries with flags added
        portugal = get_country("PT")
        portugal.flags.set([highest_priority_flag])
        andorra = get_country("AD")
        andorra.flags.set([lowest_priority_flag])
        benin = get_country("BJ")
        benin.flags.set([lowest_priority_flag])

        # Countries without flags added

        # Add additional countries to the application
        ad = CountryOnApplication(application=open_application, country=get_country("AD"))
        ad.save()
        bj = CountryOnApplication(application=open_application, country=get_country("BJ"))
        bj.save()
        at = CountryOnApplication(application=open_application, country=get_country("AT"))
        at.save()
        pt = CountryOnApplication(application=open_application, country=get_country("PT"))
        pt.save()
        # FR already on draft open application
        fr = CountryOnApplication.objects.get(application=open_application, country_id="FR")

        case = self.submit_application(open_application)

        url = reverse("cases:case", kwargs={"pk": case.id})
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case_application = response.json()["case"]["data"]
        ordered_countries = [destination["id"] for destination in case_application["destinations"]["data"]]

        # Countries are ordered by flag priority and for countries without flags, they are alphabetised
        self.assertEqual(ordered_countries, [str(pt.id), str(ad.id), str(bj.id), str(at.id), str(fr.id)])

    def test_countries_ordered_as_expected_on_standard_application(self):
        highest_priority_flag = FlagFactory(
            name="highest priority flag", level="Destination", team=self.gov_user.team, priority=0
        )
        lowest_priority_flag = FlagFactory(
            name="lowest priority flag", level="Destination", team=self.gov_user.team, priority=10
        )

        standard_application = self.create_draft_standard_application(self.organisation)

        # Third parties
        first_tp = standard_application.third_parties.first()
        first_tp.party.flags.set([highest_priority_flag])

        second_tp = self.create_party("party 2", self.organisation, PartyType.THIRD_PARTY, standard_application)
        second_tp.flags.set([lowest_priority_flag])

        third_tp = self.create_party("party 3", self.organisation, PartyType.THIRD_PARTY, standard_application)

        fourth_tp = self.create_party("party 4", self.organisation, PartyType.THIRD_PARTY, standard_application)
        fourth_tp.flags.set([lowest_priority_flag])

        # Ultimate end users
        first_ueu = self.create_party("party 1", self.organisation, PartyType.ULTIMATE_END_USER, standard_application)
        first_ueu.flags.set([highest_priority_flag])

        second_ueu = self.create_party("party 2", self.organisation, PartyType.ULTIMATE_END_USER, standard_application)
        second_ueu.flags.set([lowest_priority_flag])

        third_ueu = self.create_party("party 3", self.organisation, PartyType.ULTIMATE_END_USER, standard_application)

        fourth_ueu = self.create_party("party 4", self.organisation, PartyType.ULTIMATE_END_USER, standard_application)
        fourth_ueu.flags.set([lowest_priority_flag])

        case = self.submit_application(standard_application)

        url = reverse("cases:case", kwargs={"pk": case.id})
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case_application = response.json()["case"]["data"]
        ordered_third_parties = [third_party["id"] for third_party in case_application["third_parties"]]
        ordered_ultimate_end_users = [ueu["id"] for ueu in case_application["ultimate_end_users"]]

        # Third parties and ultimate end users are ordered by destination flag priority and for
        # parties of these types without flags, they are alphabetised
        self.assertEqual(
            ordered_third_parties,
            [str(first_tp.party.id), str(second_tp.id), str(fourth_tp.id), str(third_tp.id)],
        )

        self.assertEqual(
            ordered_ultimate_end_users,
            [str(first_ueu.id), str(second_ueu.id), str(fourth_ueu.id), str(third_ueu.id)],
        )
