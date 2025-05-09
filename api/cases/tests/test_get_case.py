from datetime import timedelta
from dateutil.parser import parse
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from api.applications.tests.factories import DenialMatchOnApplicationFactory
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import Case, CaseQueue
from lite_routing.routing_rules_internal.enums import FlagsEnum
from rest_framework import status
from freezegun import freeze_time

from api.applications.models import PartyOnApplication
from api.cases.tests.factories import CaseAssignmentFactory, FinalAdviceFactory, CountersignAdviceFactory
from api.f680.tests.factories import (
    SubmittedF680ApplicationFactory,
    F680SecurityReleaseRequestFactory,
    F680ProductFactory,
)
from api.flags.enums import SystemFlags
from api.flags.models import Flag
from api.flags.tests.factories import FlagFactory
from api.parties.enums import PartyType
from test_helpers.clients import DataTestClient
from api.staticdata.statuses.models import CaseStatus, CaseSubStatus
from api.users.models import ExporterUser


class CaseGetTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)

    def test_case_endpoint_responds_ok(self):
        case = self.submit_application(self.standard_application)
        url = reverse("cases:case", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # TODO: These tests need to assert that the *whole response* is as expected
        response_json = response.json()
        self.assertEqual(response_json["case"]["amendment_of"], None)
        self.assertEqual(response_json["case"]["superseded_by"], None)

    def test_case_endpoint_responds_ok_for_amendment(self):
        superseded_case = self.submit_application(self.standard_application)
        exporter_user = ExporterUser.objects.first()
        amendment = superseded_case.create_amendment(exporter_user)
        amendment = self.submit_application(amendment)

        url = reverse("cases:case", kwargs={"pk": superseded_case.id})
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        # TODO: These tests need to assert that the *whole response* is as expected
        self.assertEqual(response_json["case"]["amendment_of"], None)
        self.assertEqual(
            response_json["case"]["superseded_by"],
            {
                "id": str(amendment.id),
                "organisation": {
                    "id": str(amendment.organisation_id),
                    "name": amendment.organisation.name,
                },
                "reference_code": amendment.reference_code,
            },
        )

        url = reverse("cases:case", kwargs={"pk": amendment.id})
        response = self.client.get(url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(
            response_json["case"]["amendment_of"],
            {
                "id": str(superseded_case.id),
                "organisation": {
                    "id": str(superseded_case.organisation_id),
                    "name": superseded_case.organisation.name,
                },
                "reference_code": superseded_case.reference_code,
            },
        )
        self.assertEqual(response_json["case"]["superseded_by"], None)

    def test_case_basic_details_endpoint_responds_ok(self):
        case = self.submit_application(self.standard_application)
        url = reverse("cases:case_detail_basic", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        self.assertEqual(case.reference_code, response["reference_code"])
        self.assertEqual(case.organisation.name, response["organisation"]["name"])

    def test_case_copy_of_another_case_endpoint_responds_ok(self):
        self.submit_application(self.standard_application)

        copied_case = self.create_draft_standard_application(self.organisation)
        copied_case.copy_of = self.standard_application
        copied_case.save()
        self.submit_application(copied_case)

        url = reverse("cases:case", kwargs={"pk": copied_case.id})

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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
        self.assertEqual(len(response_data["case"]["data"]["third_parties"]), 1)

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
        if expected.organisation:
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

    def test_case_returns_has_activity(self):
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
        assert response.json()["case"]["latest_activity"] is None

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
        first_case_queue = CaseQueue.objects.create(case=case, queue=self.queue)
        first_case_queue.created_at = timezone.now() - timedelta(days=2)
        first_case_queue.save()
        second_queue = self.create_queue("Another Queue", self.team)
        second_case_queue = CaseQueue.objects.create(case=case, queue=second_queue)
        second_case_queue.created_at = timezone.now() - timedelta(days=1)
        second_case_queue.save()
        case.queues.set([self.queue, second_queue])

        case.submitted_at = timezone.now() - timedelta(days=2)
        case.save()
        url = reverse("cases:case", kwargs={"pk": case.id})
        response = self.client.get(url, **self.gov_headers)
        data = response.json()["case"]
        self.assertEqual(case.submitted_at, parse(data["submitted_at"]))
        self.assertEqual(str(second_queue.id), data["queue_details"][0]["id"])
        self.assertEqual(second_case_queue.created_at.date(), parse(data["queue_details"][0]["joined_queue_at"]).date())
        self.assertEqual(str(self.queue.id), data["queue_details"][1]["id"])
        self.assertEqual(first_case_queue.created_at.date(), parse(data["queue_details"][1]["joined_queue_at"]).date())

    def test_case_return_has_advice(self):
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

    def test_case_parameter_set_ignores_deleted_parties(self):
        application = self.submit_application(self.standard_application)
        case = Case.objects.get(id=application.id)

        end_user = PartyOnApplication.objects.get(application=application, party__type=PartyType.END_USER)
        end_user.party.flags.add(Flag.objects.get(id=FlagsEnum.AUSTRALIA_GROUP_CW))
        consignee = PartyOnApplication.objects.get(application=application, party__type=PartyType.END_USER)
        consignee.party.flags.add(Flag.objects.get(id=FlagsEnum.LU_COUNTER_REQUIRED))
        self.assertIn(Flag.objects.get(id=FlagsEnum.LU_COUNTER_REQUIRED), case.parameter_set())

        consignee.delete()
        self.assertNotIn(Flag.objects.get(id=FlagsEnum.LU_COUNTER_REQUIRED), case.parameter_set())

    def test_cases_endpoint_with_sub_status(self):
        case_status = CaseStatus.objects.get(status="finalised")
        case = self.submit_application(self.standard_application)
        case.status = case_status
        case.save()

        sub_status_url = reverse("applications:manage_sub_status", kwargs={"pk": case.id})

        sub_status = CaseSubStatus.objects.create(
            name="test_sub_status",
            parent_status=case_status,
        )
        data = {"sub_status": str(sub_status.pk)}

        self.client.put(sub_status_url, data=data, **self.gov_headers)

        case.refresh_from_db()

        url = reverse("cases:search")
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["results"]["cases"][0]["sub_status"]["name"], sub_status.name)

    def test_case_returns_expected_denial_matches(self):
        """
        Given a case with a denial match
        When the case is retrieved
        Then the denial match json data is as expected.
        """
        case = self.submit_application(self.standard_application)
        denial_match = DenialMatchOnApplicationFactory(application=case)
        url = reverse("cases:case", kwargs={"pk": case.id})

        expected_denial_matches = [
            {
                "id": str(denial_match.id),
                "application": str(case.id),
                "denial_entity": {
                    "id": str(denial_match.denial_entity.id),
                    "created_by": str(denial_match.denial_entity.created_by_id),
                    "name": denial_match.denial_entity.name,
                    "address": denial_match.denial_entity.address,
                    "regime_reg_ref": denial_match.denial_entity.denial.regime_reg_ref,
                    "notifying_government": denial_match.denial_entity.denial.notifying_government,
                    "country": denial_match.denial_entity.country,
                    "denial_cle": denial_match.denial_entity.denial.denial_cle,
                    "item_description": denial_match.denial_entity.denial.item_description,
                    "end_use": denial_match.denial_entity.denial.end_use,
                    "is_revoked": denial_match.denial_entity.denial.is_revoked,
                    "is_revoked_comment": denial_match.denial_entity.denial.is_revoked_comment,
                    "reason_for_refusal": denial_match.denial_entity.denial.reason_for_refusal,
                    "entity_type": denial_match.denial_entity.entity_type,
                    "reference": denial_match.denial_entity.denial.reference,
                    "denial": str(denial_match.denial_entity.denial.id),
                },
                "category": denial_match.category,
            }
        ]

        response = self.client.get(url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["case"]["data"]["denial_matches"], expected_denial_matches)

    @freeze_time("2025-01-01 12:00:01")
    def test_f680_case_no_related_records(self):
        application = SubmittedF680ApplicationFactory(
            name="some name",
        )
        url = reverse("cases:case", kwargs={"pk": application.id})

        response = self.client.get(url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_case_data = {
            "application": {"some": "json"},
            "id": str(application.id),
            "name": "some name",
            "organisation": {
                "id": str(application.organisation.id),
                "name": application.organisation.name,
                "status": application.organisation.status,
                "type": application.organisation.type,
            },
            "product": None,
            "reference_code": application.reference_code,
            "security_release_requests": [],
            "status": {"id": str(application.status.id), "key": "submitted", "value": "Submitted"},
            "submitted_at": "2025-01-01T12:00:01Z",
            "submitted_by": {
                "id": str(application.submitted_by.baseuser_ptr.id),
                "first_name": application.submitted_by.first_name,
                "last_name": application.submitted_by.last_name,
                "email": application.submitted_by.email,
                "pending": application.submitted_by.pending,
            },
            "case_type": {
                "id": str(application.case_type_id),
                "reference": {"key": "f680", "value": "MOD F680 Clearance"},
                "type": {"key": "security_clearance", "value": "Security Clearance"},
                "sub_type": {"key": "f680_clearance", "value": "MOD F680 Clearance"},
            },
            "sub_status": None,
        }
        self.assertEqual(response_data["case"]["data"], expected_case_data)

    @freeze_time("2025-01-01 12:00:01")
    def test_f680_case_related_records(self):
        application = SubmittedF680ApplicationFactory(
            name="some name",
        )
        product = F680ProductFactory()
        security_release_requests = []
        for i in range(3):
            security_release_requests.append(
                F680SecurityReleaseRequestFactory(application=application, product=product)
            )

        url = reverse("cases:case", kwargs={"pk": application.id})
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_case_data = {
            "application": {"some": "json"},
            "id": str(application.id),
            "name": "some name",
            "organisation": {
                "id": str(application.organisation.id),
                "name": application.organisation.name,
                "status": application.organisation.status,
                "type": application.organisation.type,
            },
            "product": {
                "id": str(product.id),
                "name": product.name,
                "description": product.description,
                "security_grading": {"key": product.security_grading, "value": product.get_security_grading_display()},
                "security_grading_other": product.security_grading_other,
            },
            "reference_code": application.reference_code,
            "security_release_requests": [
                {
                    "id": str(request.id),
                    "recipient": {
                        "id": str(request.recipient.id),
                        "name": request.recipient.name,
                        "address": request.recipient.address,
                        "country": {
                            "id": str(request.recipient.country_id),
                            "name": request.recipient.country.name,
                            "type": request.recipient.country.type,
                            "is_eu": request.recipient.country.is_eu,
                            "report_name": request.recipient.country.report_name,
                        },
                        "type": {"key": request.recipient.type, "value": request.recipient.get_type_display()},
                        "role": request.recipient.role,
                        "role_other": request.recipient.role_other,
                    },
                    "security_grading": {
                        "key": request.security_grading,
                        "value": request.get_security_grading_display(),
                    },
                    "security_grading_other": request.security_grading_other,
                    "approval_types": request.approval_types,
                    "intended_use": request.intended_use,
                    "product_id": str(request.product.id),
                }
                for request in security_release_requests
            ],
            "status": {"id": str(application.status.id), "key": "submitted", "value": "Submitted"},
            "submitted_at": "2025-01-01T12:00:01Z",
            "submitted_by": {
                "id": str(application.submitted_by.baseuser_ptr.id),
                "first_name": application.submitted_by.first_name,
                "last_name": application.submitted_by.last_name,
                "email": application.submitted_by.email,
                "pending": application.submitted_by.pending,
            },
            "case_type": {
                "id": str(application.case_type_id),
                "reference": {"key": "f680", "value": "MOD F680 Clearance"},
                "type": {"key": "security_clearance", "value": "Security Clearance"},
                "sub_type": {"key": "f680_clearance", "value": "MOD F680 Clearance"},
            },
            "sub_status": None,
        }
        self.assertEqual(response_data["case"]["data"], expected_case_data)
