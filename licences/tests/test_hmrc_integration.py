from unittest import mock

from cases.enums import AdviceType, AdviceLevel
from conf.settings import MAX_ATTEMPTS
from licences.libraries.hmrc_integration_operations import send_licence, HMRCIntegrationException
from licences.models import Licence
from licences.serializers.hmrc_integration import HMRCIntegrationLicenceSerializer
from licences.tasks import send_licence_to_hmrc_integration, TASK_BACK_OFF, schedule_max_tried_task_as_new_task
from test_helpers.clients import DataTestClient


class MockResponse:
    def __init__(self, json_data: str, status_code: int):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


class MockSerializer:
    def __init__(self, licence: Licence):
        self.data = {"id": str(licence.id)}


class MockTask:
    def __init__(self, attempts: int):
        self.attempts = attempts


class HMRCIntegrationSerializersTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, is_complete=True)

    def test_data_transfer_object_standard_application(self):
        data = HMRCIntegrationLicenceSerializer(self.standard_licence).data

        self._assert_dto(data, self.standard_licence)

    def test_data_transfer_object_open_application(self):
        open_application = self.create_open_application_case(self.organisation)
        self.create_advice(self.gov_user, open_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        open_licence = self.create_licence(open_application, is_complete=True)

        data = HMRCIntegrationLicenceSerializer(open_licence).data

        self._assert_dto(data, open_licence)

    def _assert_dto(self, data: dict, licence: Licence):
        self.assertEqual(len(data), 9)
        self.assertEqual(data["id"], str(licence.id))


class HMRCIntegrationOperationsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, is_complete=True)

    @mock.patch("licences.libraries.hmrc_integration_operations.post")
    @mock.patch("licences.libraries.hmrc_integration_operations.HMRCIntegrationLicenceSerializer")
    def test_send_licence_success(self, serializer, requests):
        serializer.return_value = MockSerializer(self.standard_licence)
        requests.return_value = MockResponse("", 201)

        send_licence(self.standard_licence)

        requests.assert_called_once()

    @mock.patch("licences.libraries.hmrc_integration_operations.post")
    @mock.patch("licences.libraries.hmrc_integration_operations.HMRCIntegrationLicenceSerializer")
    def test_send_licence_failure(self, serializer, requests):
        serializer.return_value = MockSerializer(self.standard_licence)
        requests.return_value = MockResponse("Bad request", 400)

        with self.assertRaises(HMRCIntegrationException) as error:
            send_licence(self.standard_licence)

        requests.assert_called_once()
        self.assertEqual(
            str(error.exception),
            f"An unexpected response was received when sending licence '{self.standard_licence.id}' changes "
            f"to HMRC Integration -> status=400, message=Bad request",
        )


class HMRCIntegrationTasksTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, self.standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        self.standard_licence = self.create_licence(self.standard_application, is_complete=True)

    @mock.patch("licences.tasks.hmrc_integration_operations.send_licence")
    def test_send_licence_to_hmrc_integration_success(self, send_licence):
        send_licence.return_value = None

        # Note: Using `.now()` operation to test code synchronously
        send_licence_to_hmrc_integration.now(str(self.standard_licence.id), is_background_task=False)

        send_licence.assert_called_once()

    @mock.patch("licences.tasks.Task.objects.get")
    @mock.patch("licences.tasks.hmrc_integration_operations.send_licence")
    def test_send_licence_to_hmrc_integration_failure(self, send_licence, task_get):
        send_licence.side_effect = HMRCIntegrationException("Recieved an unexpected response")
        task_get.return_value = MockTask(0)

        # Note: Using `.now()` operation to test code synchronously
        send_licence_to_hmrc_integration.now(str(self.standard_licence.id), is_background_task=False)

        send_licence.assert_called_once()
        task_get.assert_not_called()

    @mock.patch("licences.tasks.hmrc_integration_operations.send_licence")
    def test_send_licence_to_hmrc_integration_with_background_task_success(self, send_licence):
        send_licence.return_value = None

        # Note: Using `.now()` operation to test code synchronously
        send_licence_to_hmrc_integration.now(str(self.standard_licence.id), is_background_task=True)

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
            send_licence_to_hmrc_integration.now(str(self.standard_licence.id))

        send_licence.assert_called_once()
        task_get.assert_called_once()
        schedule_max_tried_task_as_new_task.assert_not_called()
        self.assertEqual(
            str(error.exception), f"Failed to send licence '{self.standard_licence.id}' changes to HMRC Integration",
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
            send_licence_to_hmrc_integration.now(str(self.standard_licence.id))

        send_licence.assert_called_once()
        task_get.assert_called_once()
        schedule_max_tried_task_as_new_task.assert_called_once()
        self.assertEqual(
            str(error.exception), f"Failed to send licence '{self.standard_licence.id}' changes to HMRC Integration",
        )

    @mock.patch("licences.tasks.send_licence_to_hmrc_integration")
    def test_schedule_max_tried_task_as_new_task(self, send_licence_to_hmrc_integration):
        send_licence_to_hmrc_integration.return_value = None

        schedule_max_tried_task_as_new_task(str(self.standard_licence.id))

        send_licence_to_hmrc_integration.assert_called_with(str(self.standard_licence.id), schedule=TASK_BACK_OFF)
