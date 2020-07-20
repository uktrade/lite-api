from unittest import mock
from unittest.mock import ANY

from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized
from rest_framework import status

from cases.enums import AdviceType, CaseTypeSubTypeEnum, AdviceLevel, CaseTypeEnum
from cases.models import CaseType
from conf.constants import GovPermissions
from conf.helpers import add_months
from conf.settings import MAX_ATTEMPTS, LITE_HMRC_INTEGRATION_URL, LITE_HMRC_REQUEST_TIMEOUT
from licences.apps import LicencesConfig
from licences.enums import LicenceStatus, HMRCIntegrationActionEnum, licence_status_to_hmrc_integration_action
from licences.helpers import get_approved_goods_types
from licences.libraries.hmrc_integration_operations import (
    send_licence,
    HMRCIntegrationException,
    SEND_LICENCE_ENDPOINT,
)
from licences.models import Licence
from licences.serializers.hmrc_integration import HMRCIntegrationLicenceSerializer
from licences.tasks import (
    send_licence_to_hmrc_integration,
    TASK_BACK_OFF,
    schedule_max_tried_task_as_new_task,
    schedule_licence_for_hmrc_integration,
    HMRC_INTEGRATION_QUEUE,
)
from licences.tests.factories import GoodOnLicenceFactory
from open_general_licences.helpers import issue_open_general_licence
from open_general_licences.tests.factories import OpenGeneralLicenceFactory, OpenGeneralLicenceCaseFactory
from static.countries.models import Country
from static.decisions.models import Decision
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class MockResponse:
    def __init__(self, message: str, status_code: int):
        self.json_data = message
        self.text = message
        self.status_code = status_code

    def json(self):
        return self.json_data


class MockSerializer:
    def __init__(self, licence: Licence):
        self.data = {"id": str(licence.id)}


class MockTask:
    def __init__(self, attempts: int, exists=True):
        self.attempts = attempts
        self._exists = exists

    def exists(self):
        return self._exists


class HMRCIntegrationSerializersTests(DataTestClient):
    @parameterized.expand(
        [
            [LicenceStatus.ISSUED],
            [LicenceStatus.REINSTATED],
            [LicenceStatus.SUSPENDED],
            [LicenceStatus.SURRENDERED],
            [LicenceStatus.REVOKED],
            [LicenceStatus.CANCELLED],
        ],
    )
    def test_standard_application(self, status):
        action = licence_status_to_hmrc_integration_action.get(status)
        standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        standard_licence = self.create_licence(standard_application, status=status)
        good_on_application = standard_application.goods.first()
        GoodOnLicenceFactory(
            good=good_on_application,
            licence=standard_licence,
            quantity=good_on_application.quantity,
            usage=20.0,
            value=good_on_application.value,
        )
        old_licence = None
        if action == HMRCIntegrationActionEnum.UPDATE:
            old_licence = self.create_licence(standard_application, status=LicenceStatus.CANCELLED)
            standard_application.licences.add(old_licence)

        data = HMRCIntegrationLicenceSerializer(standard_licence).data

        self._assert_dto(data, standard_licence, old_licence=old_licence)

    @parameterized.expand(
        [
            [LicenceStatus.ISSUED],
            [LicenceStatus.REINSTATED],
            [LicenceStatus.SUSPENDED],
            [LicenceStatus.SURRENDERED],
            [LicenceStatus.REVOKED],
            [LicenceStatus.CANCELLED],
        ],
    )
    def test_open_application(self, status):
        action = licence_status_to_hmrc_integration_action.get(status)
        open_application = self.create_open_application_case(self.organisation)
        self.create_advice(self.gov_user, open_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        open_licence = self.create_licence(open_application, status=status)
        old_licence = None
        if action == HMRCIntegrationActionEnum.UPDATE:
            old_licence = self.create_licence(open_application, status=LicenceStatus.CANCELLED)
            open_application.licences.add(old_licence)

        data = HMRCIntegrationLicenceSerializer(open_licence).data

        self._assert_dto(data, open_licence, old_licence)

    @parameterized.expand(
        [
            [LicenceStatus.ISSUED],
            [LicenceStatus.REINSTATED],
            [LicenceStatus.SUSPENDED],
            [LicenceStatus.SURRENDERED],
            [LicenceStatus.REVOKED],
            [LicenceStatus.CANCELLED],
        ],
    )
    def test_ogl_application(self, status):
        action = licence_status_to_hmrc_integration_action.get(status)
        open_general_licence = OpenGeneralLicenceFactory(case_type=CaseType.objects.get(id=CaseTypeEnum.OGEL.id))
        open_general_licence_case = OpenGeneralLicenceCaseFactory(
            open_general_licence=open_general_licence,
            site=self.organisation.primary_site,
            organisation=self.organisation,
        )
        open_general_licence_licence = Licence.objects.get(case=open_general_licence_case)

        if action == HMRCIntegrationActionEnum.UPDATE:
            # Cancel the original & issue a new OGL Licence
            open_general_licence_licence.cancel()
            new_licence = issue_open_general_licence(open_general_licence_case)
            data = HMRCIntegrationLicenceSerializer(new_licence).data
            self._assert_dto(data, new_licence, old_licence=open_general_licence_licence)
        else:
            data = HMRCIntegrationLicenceSerializer(open_general_licence_licence).data
            self._assert_dto(data, open_general_licence_licence)

    def _assert_dto(self, data, licence, old_licence=None):
        if old_licence:
            self.assertEqual(len(data), 10)
            self.assertEqual(data["old_id"], str(old_licence.id))
        else:
            self.assertEqual(len(data), 9)

        self.assertEqual(data["id"], str(licence.id))
        self.assertEqual(data["reference"], licence.reference_code)
        self.assertEqual(data["type"], licence.case.case_type.reference)
        self.assertEqual(data["action"], licence_status_to_hmrc_integration_action.get(licence.status))
        self.assertEqual(data["start_date"], licence.start_date.strftime("%Y-%m-%d"))
        self.assertEqual(data["end_date"], add_months(licence.start_date, licence.duration, "%Y-%m-%d"))

        self._assert_organisation(data, licence.case.organisation)

        if licence.case.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
            self._assert_end_user(data, licence.case.end_user.party)
            self._assert_goods_on_licence(data, licence.goods.all())
            self.assertEqual(data["id"], str(licence.id))
        elif licence.case.case_type.id in CaseTypeEnum.OPEN_GENERAL_LICENCE_IDS:
            self._assert_countries(
                data, licence.case.opengenerallicencecase.open_general_licence.countries.order_by("name")
            )
        elif licence.case.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
            self._assert_countries(
                data, Country.objects.filter(countries_on_application__application=licence.case).order_by("name")
            )
            self._assert_goods_types(data, get_approved_goods_types(licence.case.baseapplication))

    def _assert_organisation(self, data, organisation):
        self.assertEqual(
            data["organisation"],
            {
                "id": str(organisation.id),
                "name": organisation.name,
                "address": {
                    "line_1": organisation.primary_site.name,
                    "line_2": organisation.primary_site.address.address_line_1,
                    "line_3": organisation.primary_site.address.address_line_2,
                    "line_4": organisation.primary_site.address.city,
                    "line_5": organisation.primary_site.address.region,
                    "postcode": organisation.primary_site.address.postcode,
                    "country": {
                        "id": organisation.primary_site.address.country.id,
                        "name": organisation.primary_site.address.country.name,
                    },
                },
            },
        )

    def _assert_end_user(self, data, end_user):
        self.assertEqual(
            data["end_user"],
            {
                "name": end_user.name,
                "address": {
                    "line_1": end_user.address,
                    "country": {"id": end_user.country.id, "name": end_user.country.name},
                },
            },
        )

    def _assert_countries(self, data, countries):
        self.assertEqual(data["countries"], [{"id": country.id, "name": country.name} for country in countries])

    def _assert_goods_types(self, data, goods):
        self.assertEqual(
            data["goods"],
            [{"id": str(good.id), "description": good.description, "usage": good.usage} for good in goods],
        )

    def _assert_goods_on_licence(self, data, goods):
        data = data["goods"]
        for i in range(len(goods)):
            good_on_licence = goods[i]
            self.assertEqual(data[i]["id"], str(good_on_licence.good.good.id))
            self.assertEqual(data[i]["usage"], good_on_licence.usage)
            self.assertEqual(data[i]["description"], good_on_licence.good.good.description)
            self.assertEqual(data[i]["unit"], good_on_licence.good.unit)
            self.assertEqual(data[i]["quantity"], good_on_licence.quantity)
            self.assertEqual(data[i]["value"], good_on_licence.value)


class HMRCIntegrationOperationsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        status = LicenceStatus.ISSUED
        self.hmrc_integration_status = licence_status_to_hmrc_integration_action.get(status)
        self.standard_licence = self.create_licence(self.standard_application, status=status)

    @mock.patch("licences.libraries.hmrc_integration_operations.post")
    @mock.patch("licences.libraries.hmrc_integration_operations.HMRCIntegrationLicenceSerializer")
    def test_send_licence_success_201(self, serializer, requests_post):
        serializer.return_value = MockSerializer(self.standard_licence)
        original_hmrc_integration_sent_at = self.standard_licence.hmrc_integration_sent_at  # Should be None
        requests_post.return_value = MockResponse("", 201)

        send_licence(self.standard_licence, self.hmrc_integration_status)

        requests_post.assert_called_once()
        self.assertIsNotNone(self.standard_licence.hmrc_integration_sent_at)
        self.assertNotEqual(self.standard_licence.hmrc_integration_sent_at, original_hmrc_integration_sent_at)

    @mock.patch("licences.libraries.hmrc_integration_operations.post")
    @mock.patch("licences.libraries.hmrc_integration_operations.HMRCIntegrationLicenceSerializer")
    def test_send_licence_success_200(self, serializer, requests_post):
        serializer.return_value = MockSerializer(self.standard_licence)
        original_hmrc_integration_sent_at = self.standard_licence.hmrc_integration_sent_at  # Should not be None
        requests_post.return_value = MockResponse("", 200)

        send_licence(self.standard_licence, self.hmrc_integration_status)

        requests_post.assert_called_once()
        self.assertEqual(self.standard_licence.hmrc_integration_sent_at, original_hmrc_integration_sent_at)

    @mock.patch("licences.libraries.hmrc_integration_operations.post")
    @mock.patch("licences.libraries.hmrc_integration_operations.HMRCIntegrationLicenceSerializer")
    def test_send_licence_failure(self, serializer, requests_post):
        serializer.return_value = MockSerializer(self.standard_licence)
        requests_post.return_value = MockResponse("Bad request", 400)

        with self.assertRaises(HMRCIntegrationException) as error:
            send_licence(self.standard_licence, self.hmrc_integration_status)

        requests_post.assert_called_once()
        self.assertEqual(
            str(error.exception),
            f"An unexpected response was received when sending licence '{self.standard_licence.id}', "
            f"action '{self.hmrc_integration_status}' to HMRC Integration -> status=400, message=Bad request",
        )
        self.assertIsNone(self.standard_licence.hmrc_integration_sent_at)


@mock.patch("licences.models.LITE_HMRC_INTEGRATION_ENABLED", True)
class HMRCIntegrationLicenceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, status=LicenceStatus.ISSUED)

    @mock.patch("licences.tasks.schedule_licence_for_hmrc_integration")
    def test_save_licence_calls_schedule_licence_for_hmrc_integration(self, schedule_licence_for_hmrc_integration):
        schedule_licence_for_hmrc_integration.return_value = None

        self.standard_licence.save(send_status_change_to_hmrc=True)

        schedule_licence_for_hmrc_integration.assert_called_with(
            str(self.standard_licence.id), licence_status_to_hmrc_integration_action.get(self.standard_licence.status),
        )

    @mock.patch("licences.tasks.schedule_licence_for_hmrc_integration")
    def test_save_licence_does_not_call_schedule_licence_for_hmrc_integration(
        self, schedule_licence_for_hmrc_integration
    ):
        schedule_licence_for_hmrc_integration.return_value = None

        self.standard_licence.save()

        schedule_licence_for_hmrc_integration.assert_not_called()

    @mock.patch("licences.tasks.schedule_licence_for_hmrc_integration")
    def test_licence_surrender_calls_schedule_licence_for_hmrc_integration(self, schedule_licence_for_hmrc_integration):
        schedule_licence_for_hmrc_integration.return_value = None

        self.standard_licence.surrender()

        schedule_licence_for_hmrc_integration.assert_called_with(
            str(self.standard_licence.id), licence_status_to_hmrc_integration_action.get(self.standard_licence.status),
        )

    @mock.patch("licences.tasks.schedule_licence_for_hmrc_integration")
    def test_licence_cancel_calls_schedule_licence_for_hmrc_integration(self, schedule_licence_for_hmrc_integration):
        schedule_licence_for_hmrc_integration.return_value = None

        self.standard_licence.cancel()

        schedule_licence_for_hmrc_integration.assert_called_with(
            str(self.standard_licence.id), licence_status_to_hmrc_integration_action.get(self.standard_licence.status),
        )

    @mock.patch("licences.tasks.schedule_licence_for_hmrc_integration")
    def test_licence_revoke_calls_schedule_licence_for_hmrc_integration(self, schedule_licence_for_hmrc_integration):
        schedule_licence_for_hmrc_integration.return_value = None

        self.standard_licence.revoke()

        schedule_licence_for_hmrc_integration.assert_called_with(
            str(self.standard_licence.id), licence_status_to_hmrc_integration_action.get(self.standard_licence.status),
        )

    @mock.patch("licences.tasks.schedule_licence_for_hmrc_integration")
    def test_licence_expire_calls_schedule_licence_for_hmrc_integration(self, schedule_licence_for_hmrc_integration):
        schedule_licence_for_hmrc_integration.return_value = None

        self.standard_licence.revoke()

        schedule_licence_for_hmrc_integration.assert_called_with(
            str(self.standard_licence.id), licence_status_to_hmrc_integration_action.get(self.standard_licence.status),
        )

    @mock.patch("licences.tasks.schedule_licence_for_hmrc_integration")
    def test_licence_exhaust_calls_schedule_licence_for_hmrc_integration(self, schedule_licence_for_hmrc_integration):
        schedule_licence_for_hmrc_integration.return_value = None

        self.standard_licence.exhaust()

        schedule_licence_for_hmrc_integration.assert_called_with(
            str(self.standard_licence.id), licence_status_to_hmrc_integration_action.get(self.standard_licence.status),
        )


class HMRCIntegrationTasksTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        status = LicenceStatus.ISSUED
        self.hmrc_integration_status = licence_status_to_hmrc_integration_action.get(status)
        self.standard_licence = self.create_licence(self.standard_application, status=status)

    @mock.patch("licences.tasks.BACKGROUND_TASK_ENABLED", False)
    @mock.patch("licences.tasks.send_licence_to_hmrc_integration.now")
    def test_schedule_licence_for_hmrc_integration(self, send_licence_to_hmrc_integration_now):
        send_licence_to_hmrc_integration_now.return_value = None

        schedule_licence_for_hmrc_integration(
            str(self.standard_licence.id), self.hmrc_integration_status,
        )

        send_licence_to_hmrc_integration_now.assert_called_with(
            str(self.standard_licence.id), self.hmrc_integration_status, scheduled_as_background_task=False,
        )

    @mock.patch("licences.tasks.BACKGROUND_TASK_ENABLED", True)
    @mock.patch("licences.tasks.send_licence_to_hmrc_integration")
    @mock.patch("licences.tasks.Task.objects.filter")
    def test_schedule_licence_for_hmrc_integration_as_background_task(
        self, task_filter, send_licence_to_hmrc_integration
    ):
        task_filter.return_value = MockTask(0, exists=False)
        send_licence_to_hmrc_integration.return_value = None

        schedule_licence_for_hmrc_integration(str(self.standard_licence.id), self.hmrc_integration_status)

        task_filter.assert_called_with(
            queue=HMRC_INTEGRATION_QUEUE,
            task_params=f'[["{self.standard_licence.id}", "{self.hmrc_integration_status}"], {{}}]',
        )
        send_licence_to_hmrc_integration.assert_called_with(str(self.standard_licence.id), self.hmrc_integration_status)

    @mock.patch("licences.tasks.BACKGROUND_TASK_ENABLED", True)
    @mock.patch("licences.tasks.send_licence_to_hmrc_integration")
    @mock.patch("licences.tasks.Task.objects.filter")
    def test_schedule_licence_for_hmrc_integration_as_background_task_already_existing(
        self, task_filter, send_licence_to_hmrc_integration
    ):
        task_filter.return_value = MockTask(0, exists=True)
        send_licence_to_hmrc_integration.return_value = None

        schedule_licence_for_hmrc_integration(str(self.standard_licence.id), self.hmrc_integration_status)

        task_filter.assert_called_with(
            queue=HMRC_INTEGRATION_QUEUE,
            task_params=f'[["{self.standard_licence.id}", "{self.hmrc_integration_status}"], {{}}]',
        )
        send_licence_to_hmrc_integration.assert_not_called()

    @mock.patch("licences.tasks.hmrc_integration_operations.send_licence")
    def test_send_licence_to_hmrc_integration_success(self, send_licence):
        send_licence.return_value = None

        # Note: Using `.now()` operation to test code synchronously
        send_licence_to_hmrc_integration.now(str(self.standard_licence.id), self.hmrc_integration_status)

        send_licence.assert_called_with(self.standard_licence, self.hmrc_integration_status)

    @mock.patch("licences.tasks.Task.objects.get")
    @mock.patch("licences.tasks.hmrc_integration_operations.send_licence")
    def test_send_licence_to_hmrc_integration_failure(self, send_licence, task_get):
        send_licence.side_effect = HMRCIntegrationException("Recieved an unexpected response")
        task_get.return_value = MockTask(0)

        # Note: Using `.now()` operation to test code synchronously
        send_licence_to_hmrc_integration.now(
            str(self.standard_licence.id), self.hmrc_integration_status, scheduled_as_background_task=False,
        )

        send_licence.assert_called_with(self.standard_licence, self.hmrc_integration_status)
        task_get.assert_not_called()

    @mock.patch("licences.tasks.hmrc_integration_operations.send_licence")
    def test_send_licence_to_hmrc_integration_with_background_task_success(self, send_licence):
        send_licence.return_value = None

        # Note: Using `.now()` operation to test code synchronously
        send_licence_to_hmrc_integration.now(str(self.standard_licence.id), self.hmrc_integration_status)

        send_licence.assert_called_once()

    @mock.patch("licences.tasks.schedule_max_tried_task_as_new_task")
    @mock.patch("licences.tasks.Task.objects.get")
    @mock.patch("licences.tasks.hmrc_integration_operations.send_licence")
    def test_send_licence_to_hmrc_integration_with_background_task_failure(
        self, send_licence, task_get, schedule_max_tried_task_as_new_task
    ):
        send_licence.side_effect = HMRCIntegrationException("Recieved an unexpected response")
        task_get.return_value = MockTask(0)
        schedule_max_tried_task_as_new_task.return_value = None

        with self.assertRaises(Exception) as error:
            # Note: Using `.now()` operation to test code synchronously
            send_licence_to_hmrc_integration.now(str(self.standard_licence.id), self.hmrc_integration_status)

        send_licence.assert_called_once()
        task_get.assert_called_with(
            queue=HMRC_INTEGRATION_QUEUE,
            task_params=f'[["{self.standard_licence.id}", "{ self.hmrc_integration_status}"], {{}}]',
        )
        schedule_max_tried_task_as_new_task.assert_not_called()
        self.assertEqual(
            str(error.exception),
            f"Failed to send licence '{self.standard_licence.id}', action '{self.hmrc_integration_status}' "
            f"to HMRC Integration",
        )

    @mock.patch("licences.tasks.schedule_max_tried_task_as_new_task")
    @mock.patch("licences.tasks.Task.objects.get")
    @mock.patch("licences.tasks.hmrc_integration_operations.send_licence")
    def test_send_licence_to_hmrc_integration_with_background_task_failure_max_attempts(
        self, send_licence, task_get, schedule_max_tried_task_as_new_task
    ):
        send_licence.side_effect = HMRCIntegrationException("Recieved an unexpected response")
        task_get.return_value = MockTask(MAX_ATTEMPTS - 1)  # Make the current task attempt 1 less than MAX_ATTEMPTS
        schedule_max_tried_task_as_new_task.return_value = None

        with self.assertRaises(Exception) as error:
            # Note: Using `.now()` operation to test code synchronously
            send_licence_to_hmrc_integration.now(
                str(self.standard_licence.id), self.hmrc_integration_status,
            )

        send_licence.assert_called_once()
        task_get.assert_called_with(
            queue=HMRC_INTEGRATION_QUEUE,
            task_params=f'[["{self.standard_licence.id}", "{self.hmrc_integration_status}"], {{}}]',
        )
        schedule_max_tried_task_as_new_task.assert_called_with(
            str(self.standard_licence.id), self.hmrc_integration_status,
        )
        self.assertEqual(
            str(error.exception),
            f"Failed to send licence '{self.standard_licence.id}', action "
            f"'{self.hmrc_integration_status}' to HMRC Integration",
        )

    @mock.patch("licences.tasks.send_licence_to_hmrc_integration")
    def test_schedule_max_tried_task_as_new_task(self, send_licence_to_hmrc_integration):
        send_licence_to_hmrc_integration.return_value = None

        schedule_max_tried_task_as_new_task(str(self.standard_licence.id), self.hmrc_integration_status)

        send_licence_to_hmrc_integration.assert_called_with(
            str(self.standard_licence.id), self.hmrc_integration_status, schedule=TASK_BACK_OFF
        )

    @mock.patch("licences.tasks.schedule_licence_for_hmrc_integration")
    def test_initialize_background_task_already_scheduled(self, schedule_licence_for_hmrc_integration):
        schedule_licence_for_hmrc_integration.return_value = None

        # When the application is restarted it will trigger this function
        LicencesConfig.schedule_not_sent_licences()

        schedule_licence_for_hmrc_integration.assert_called_with(
            str(self.standard_licence.id), self.hmrc_integration_status
        )


@mock.patch("licences.tasks.BACKGROUND_TASK_ENABLED", False)
@mock.patch("licences.models.LITE_HMRC_INTEGRATION_ENABLED", True)
class HMRCIntegrationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])

    @mock.patch("conf.requests.requests.request")
    def test_approve_standard_application_licence_success(self, request):
        request.return_value = MockResponse("", 201)
        standard_application, standard_licence = self._create_licence_for_submission(
            self.create_standard_application_case
        )
        expected_insert_json = HMRCIntegrationLicenceSerializer(standard_licence).data
        expected_insert_json["action"] = HMRCIntegrationActionEnum.INSERT

        url = reverse("cases:finalise", kwargs={"pk": standard_application.id})
        response = self.client.put(url, data={}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        request.assert_called_once_with(
            "POST",
            f"{LITE_HMRC_INTEGRATION_URL}{SEND_LICENCE_ENDPOINT}",
            json={"licence": expected_insert_json},
            headers=ANY,
            timeout=LITE_HMRC_REQUEST_TIMEOUT,
        )

    @mock.patch("conf.requests.requests.request")
    def test_approve_open_application_licence_success(self, request):
        request.return_value = MockResponse("", 201)
        open_application, open_licence = self._create_licence_for_submission(self.create_open_application_case)
        expected_insert_json = HMRCIntegrationLicenceSerializer(open_licence).data
        expected_insert_json["action"] = HMRCIntegrationActionEnum.INSERT

        url = reverse("cases:finalise", kwargs={"pk": open_application.id})
        response = self.client.put(url, data={}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        request.assert_called_once_with(
            "POST",
            f"{LITE_HMRC_INTEGRATION_URL}{SEND_LICENCE_ENDPOINT}",
            json={"licence": expected_insert_json},
            headers=ANY,
            timeout=LITE_HMRC_REQUEST_TIMEOUT,
        )

    @mock.patch("conf.requests.requests.request")
    def test_surrender_licence_success(self, request):
        request.return_value = MockResponse("", 201)
        standard_application, standard_licence = self._create_licence_for_submission(
            self.create_standard_application_case
        )
        # Set Case to Finalised so it can be surrendered
        standard_application.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        standard_application.save()
        standard_licence.status = LicenceStatus.ISSUED
        standard_licence.save()
        expected_insert_json = HMRCIntegrationLicenceSerializer(standard_licence).data
        expected_insert_json["action"] = HMRCIntegrationActionEnum.CANCEL

        url = reverse("applications:manage_status", kwargs={"pk": standard_application.id})
        response = self.client.put(url, data={"status": CaseStatusEnum.SURRENDERED}, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request.assert_called_once_with(
            "POST",
            f"{LITE_HMRC_INTEGRATION_URL}{SEND_LICENCE_ENDPOINT}",
            json={"licence": expected_insert_json},
            headers=ANY,
            timeout=LITE_HMRC_REQUEST_TIMEOUT,
        )

    @mock.patch("conf.requests.requests.request")
    def test_revoke_licence_success(self, request):
        request.return_value = MockResponse("", 201)
        standard_application, standard_licence = self._create_licence_for_submission(
            self.create_standard_application_case
        )
        # Set Case to Finalised so it can be revoked
        standard_application.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        standard_application.save()
        # Give Gov User permission to change status of a Finalised Case
        self.gov_user.role.permissions.add(GovPermissions.REOPEN_CLOSED_CASES.name)
        standard_licence.status = LicenceStatus.ISSUED
        standard_licence.save()
        expected_insert_json = HMRCIntegrationLicenceSerializer(standard_licence).data
        expected_insert_json["action"] = HMRCIntegrationActionEnum.CANCEL

        url = reverse("applications:manage_status", kwargs={"pk": standard_application.id})
        response = self.client.put(url, data={"status": CaseStatusEnum.REVOKED}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request.assert_called_once_with(
            "POST",
            f"{LITE_HMRC_INTEGRATION_URL}{SEND_LICENCE_ENDPOINT}",
            json={"licence": expected_insert_json},
            headers=ANY,
            timeout=LITE_HMRC_REQUEST_TIMEOUT,
        )

    @mock.patch("conf.requests.requests.request")
    def test_create_ogel_licence_success(self, request):
        request.return_value = MockResponse("", 201)
        open_general_licence = OpenGeneralLicenceFactory(case_type=CaseType.objects.get(id=CaseTypeEnum.OGEL.id))
        open_general_licence_case = OpenGeneralLicenceCaseFactory(
            open_general_licence=open_general_licence,
            site=self.organisation.primary_site,
            organisation=self.organisation,
        )
        open_general_licence_licence = Licence.objects.get(case=open_general_licence_case)
        expected_insert_json = HMRCIntegrationLicenceSerializer(open_general_licence_licence).data
        expected_insert_json["action"] = HMRCIntegrationActionEnum.INSERT

        request.assert_called_with(
            "POST",
            f"{LITE_HMRC_INTEGRATION_URL}{SEND_LICENCE_ENDPOINT}",
            json={"licence": expected_insert_json},
            headers=ANY,
            timeout=LITE_HMRC_REQUEST_TIMEOUT,
        )

    @mock.patch("conf.requests.requests.request")
    def test_reinstate_licence_success(self, request):
        request.return_value = MockResponse("", 201)
        # Create Case with Licence
        standard_application, standard_licence_1 = self._create_licence_for_submission(
            self.create_standard_application_case
        )
        standard_licence_1.status = LicenceStatus.ISSUED
        standard_licence_1.save()
        # Create second Licence for Case
        _, standard_licence_2 = self._create_licence_for_submission(self.create_standard_application_case)
        # Temporarily manipulate second Licence so it can be used to build 'expected data' in the request
        standard_licence_2.case = standard_application
        standard_licence_2.status = LicenceStatus.REINSTATED
        standard_licence_2.save()
        # Build the 'expected data' from second Licence
        expected_reinstate_json = HMRCIntegrationLicenceSerializer(standard_licence_2).data
        expected_reinstate_json["action"] = HMRCIntegrationActionEnum.UPDATE
        # The request to HMRC Integration should contain the old Licence's ID
        expected_reinstate_json["old_id"] = str(standard_licence_1.id)
        # Revert second Licence back to a status required for `/cases/finalise/`
        standard_licence_2.status = LicenceStatus.DRAFT
        standard_licence_2.save()

        url = reverse("cases:finalise", kwargs={"pk": standard_application.id})
        response = self.client.put(url, data={}, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        request.assert_called_once_with(
            "POST",
            f"{LITE_HMRC_INTEGRATION_URL}{SEND_LICENCE_ENDPOINT}",
            json={"licence": expected_reinstate_json},
            headers=ANY,
            timeout=LITE_HMRC_REQUEST_TIMEOUT,
        )

    def _create_licence_for_submission(self, create_application_case_callback):
        application = create_application_case_callback(self.organisation)
        application = application.get_case()
        licence = self.create_licence(application, status=LicenceStatus.DRAFT)
        self.create_advice(self.gov_user, application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        template = self.create_letter_template(
            name=f"{timezone.now()}",
            case_types=[application.case_type],
            decisions=[Decision.objects.get(name=AdviceType.APPROVE)],
        )
        self.create_generated_case_document(application, template, advice_type=AdviceType.APPROVE, licence=licence)

        return application, licence
