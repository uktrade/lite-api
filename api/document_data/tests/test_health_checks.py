import celery
import datetime
import uuid

from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone

from rest_framework.test import APITestCase

from freezegun import freeze_time
from parameterized import parameterized

from api.conf.celery import BACKUP_DOCUMENT_DATA_SCHEDULE_NAME
from api.documents.tests.factories import DocumentFactory
from api.document_data.health_checks import (
    BackupDocumentDataHealthCheckBackend,
    BackupDocumentDataHealthCheckException,
)
from api.document_data.models import (
    BackupLog,
    DocumentData,
)


@override_settings(BACKUP_DOCUMENT_DATA_TO_DB=True)
class TestBackupDocumentDataHealthcheckBackend(APITestCase):
    def setUp(self):
        super().setUp()

        self.backend = BackupDocumentDataHealthCheckBackend()

    @override_settings(BACKUP_DOCUMENT_DATA_TO_DB=False)
    def test_backup_document_data_healthcheck_backup_off(self):
        self.assertIsNone(self.backend.check_status())

    def test_backup_document_data_healthcheck_no_backup_log(self):
        self.assertEqual(BackupLog.objects.count(), 0)
        self.assertIsNone(self.backend.check_status())

    @parameterized.expand(
        [
            celery.states.STARTED,
            celery.states.RETRY,
            celery.states.PENDING,
        ]
    )
    @patch("api.document_data.models.AsyncResult")
    def test_backup_document_data_task_running_state(self, running_state, mock_AsyncResult):
        task_id = uuid.uuid4()
        BackupLog.objects.create(task_id=task_id)
        mock_AsyncResult().status = running_state
        self.assertIsNone(self.backend.check_status())
        mock_AsyncResult.assert_called_with(str(task_id))

    @parameterized.expand(
        [
            celery.states.FAILURE,
            celery.states.REVOKED,
        ]
    )
    @patch("api.document_data.models.AsyncResult")
    def test_backup_document_data_task_failure_state(self, failure_state, mock_AsyncResult):
        task_id = uuid.uuid4()
        BackupLog.objects.create(task_id=task_id)
        mock_AsyncResult().status = failure_state
        with self.assertRaises(BackupDocumentDataHealthCheckException):
            self.backend.check_status()
        mock_AsyncResult.assert_called_with(str(task_id))

    @patch("api.document_data.health_checks.app")
    def test_backup_document_data_not_run_today(self, mock_app):
        task_id = uuid.uuid4()
        ended_at = timezone.datetime(
            2024,
            2,
            26,
            2,
            0,
            0,
            tzinfo=timezone.timezone.utc,
        )
        BackupLog.objects.create(
            ended_at=ended_at,
            task_id=task_id,
        )
        mock_remaining_estimate = mock_app.conf.beat_schedule[BACKUP_DOCUMENT_DATA_SCHEDULE_NAME][
            "schedule"
        ].remaining_estimate
        mock_remaining_estimate.return_value = timezone.timedelta(hours=-8)
        with freeze_time("2024-02-26 10:00:00"), self.assertRaises(BackupDocumentDataHealthCheckException):
            self.backend.check_status()
        mock_remaining_estimate.assert_called_with(ended_at)

    @patch("api.document_data.health_checks.app")
    def test_backup_document_data_missing_files_in_backup(self, mock_app):
        task_id = uuid.uuid4()
        ended_at = timezone.datetime(
            2024,
            2,
            26,
            2,
            0,
            0,
            tzinfo=timezone.timezone.utc,
        )
        BackupLog.objects.create(
            ended_at=ended_at,
            task_id=task_id,
        )
        DocumentFactory.create(
            created_at=timezone.datetime(
                2024,
                2,
                25,
                14,
                0,
                0,
            ),
            safe=True,
        )
        mock_remaining_estimate = mock_app.conf.beat_schedule[BACKUP_DOCUMENT_DATA_SCHEDULE_NAME][
            "schedule"
        ].remaining_estimate
        mock_remaining_estimate.return_value = timezone.timedelta(hours=16)
        with freeze_time("2024-02-26 10:00:00"), self.assertRaises(BackupDocumentDataHealthCheckException):
            self.backend.check_status()

    @patch("api.document_data.health_checks.app")
    def test_backup_document_data_unsafe_files_ignored(self, mock_app):
        task_id = uuid.uuid4()
        ended_at = timezone.datetime(
            2024,
            2,
            26,
            2,
            0,
            0,
            tzinfo=timezone.timezone.utc,
        )
        BackupLog.objects.create(
            ended_at=ended_at,
            task_id=task_id,
        )
        DocumentFactory.create(
            created_at=timezone.datetime(
                2024,
                2,
                25,
                14,
                0,
                0,
            ),
            safe=False,
        )
        mock_remaining_estimate = mock_app.conf.beat_schedule[BACKUP_DOCUMENT_DATA_SCHEDULE_NAME][
            "schedule"
        ].remaining_estimate
        mock_remaining_estimate.return_value = timezone.timedelta(hours=16)
        self.assertIsNone(self.backend.check_status())

    @patch("api.document_data.health_checks.app")
    def test_backup_document_data_files_created_after_last_backup_ignored(self, mock_app):
        task_id = uuid.uuid4()
        started_at = timezone.datetime(
            2024,
            2,
            26,
            1,
            30,
            0,
            tzinfo=timezone.timezone.utc,
        )
        ended_at = timezone.datetime(
            2024,
            2,
            26,
            2,
            0,
            0,
            tzinfo=timezone.timezone.utc,
        )
        backup_log = BackupLog.objects.create(
            ended_at=ended_at,
            task_id=task_id,
        )
        backup_log.started_at = started_at
        backup_log.save()
        DocumentFactory.create(
            created_at=ended_at + timezone.timedelta(hours=1),
            safe=True,
        )
        mock_remaining_estimate = mock_app.conf.beat_schedule[BACKUP_DOCUMENT_DATA_SCHEDULE_NAME][
            "schedule"
        ].remaining_estimate
        mock_remaining_estimate.return_value = timezone.timedelta(hours=16)
        self.assertIsNone(self.backend.check_status())

    @patch("api.document_data.health_checks.app")
    def test_backup_document_data_files_all_files_backed_up(self, mock_app):
        task_id = uuid.uuid4()
        ended_at = timezone.datetime(
            2024,
            2,
            26,
            2,
            0,
            0,
            tzinfo=timezone.timezone.utc,
        )
        BackupLog.objects.create(
            ended_at=ended_at,
            task_id=task_id,
        )
        document = DocumentFactory.create(
            created_at=ended_at - timezone.timedelta(hours=5),
            safe=True,
        )
        DocumentData.objects.create(
            last_modified=timezone.now(),
            s3_key=document.s3_key,
        )
        mock_remaining_estimate = mock_app.conf.beat_schedule[BACKUP_DOCUMENT_DATA_SCHEDULE_NAME][
            "schedule"
        ].remaining_estimate
        mock_remaining_estimate.return_value = timezone.timedelta(hours=16)
        self.assertIsNone(self.backend.check_status())

    @patch("api.document_data.health_checks.app")
    def test_backup_document_data_files_created_during_backup_ignored(self, mock_app):
        task_id = uuid.uuid4()
        started_at = timezone.datetime(
            2024,
            2,
            26,
            1,
            30,
            0,
            tzinfo=timezone.timezone.utc,
        )
        ended_at = timezone.datetime(
            2024,
            2,
            26,
            2,
            0,
            0,
            tzinfo=timezone.timezone.utc,
        )
        backup_log = BackupLog.objects.create(
            ended_at=ended_at,
            task_id=task_id,
        )
        backup_log.started_at = started_at
        backup_log.save()
        DocumentFactory.create(
            created_at=started_at + timezone.timedelta(minutes=5),
            safe=True,
        )
        mock_remaining_estimate = mock_app.conf.beat_schedule[BACKUP_DOCUMENT_DATA_SCHEDULE_NAME][
            "schedule"
        ].remaining_estimate
        mock_remaining_estimate.return_value = timezone.timedelta(hours=16)
        self.assertIsNone(self.backend.check_status())

    @parameterized.expand(
        [
            ("2024-05-22 01:49:00", -1),
            ("2024-05-22 02:55:00", -1),
            ("2024-05-22 14:35:00", -1),
        ]
    )
    def test_bst_handled_correctly(self, check_status_time, tz_offset):
        task_id = uuid.uuid4()

        # We run the cron task at 2am but celery/django correctly handles our
        # timezone changes so that this shifts to 1am in UTC when we are in BST
        # We need to make sure that the healthcheck takes this into account
        started_at = timezone.datetime(
            2024,
            5,
            22,
            1,
            0,
            0,
            tzinfo=timezone.timezone.utc,
        )
        ended_at = timezone.datetime(
            2024,
            5,
            22,
            1,
            50,
            52,
            tzinfo=timezone.timezone.utc,
        )
        backup_log = BackupLog.objects.create(
            ended_at=ended_at,
            task_id=task_id,
        )
        backup_log.started_at = started_at
        backup_log.save()

        with freeze_time(check_status_time, tz_offset=tz_offset):
            self.assertIsNone(self.backend.check_status())
