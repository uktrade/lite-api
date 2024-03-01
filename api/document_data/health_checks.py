import celery

from django.conf import settings
from django.utils import timezone

from api.conf.celery import (
    app,
    BACKUP_DOCUMENT_DATA_SCHEDULE_NAME,
)

from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import HealthCheckException

from api.documents.models import Document
from api.document_data.models import BackupLog, DocumentData


class BackupDocumentDataHealthCheckException(HealthCheckException):
    message_type = "backup documents error"


class BackupDocumentDataHealthCheckBackend(BaseHealthCheckBackend):
    # This isn't critical because ideally we don't want to get a P1 alert as
    # people outside of our team will presume this means that the system is down
    # which it isn't, however we want to receive alerts via Sentry to let us
    # know this has failed.
    critical_service = False

    def check_status(self):
        if not settings.BACKUP_DOCUMENT_DATA_TO_DB:
            return

        if not BackupLog.objects.exists():
            # This will only occur before our first run.
            # Treat this as a very short lived edge case that isn't a sign of an
            # error.
            return

        latest_backup_log = BackupLog.objects.latest()
        if not latest_backup_log.ended_at:
            # If we find that we have a backup log without an end date then we
            # can assume that the task is either running or has completely
            # failed in some way.
            async_result = latest_backup_log.get_async_result()
            if async_result.status in [
                celery.states.STARTED,
                celery.states.RETRY,
                celery.states.PENDING,
            ]:
                # If the task has pending, started or is retrying then we should
                # just wait until it's finished to check everything else so wait
                # until the next healthcheck to roll around.
                return

            # If it's not running then we can presume that some kind of error
            # occurred and the task bailed out
            raise BackupDocumentDataHealthCheckException(
                f"Latest backup ended with status {async_result.status}",
            )

        # If we have an end date then we can ask celery when we think it's next
        # going to run.
        # If the date is in the past then it means the task that should have
        # run previously hasn't for some reason.
        backup_schedule = app.conf.beat_schedule[BACKUP_DOCUMENT_DATA_SCHEDULE_NAME]["schedule"]
        next_run_delta = backup_schedule.remaining_estimate(latest_backup_log.ended_at)
        now = timezone.now()
        next_run = now + next_run_delta
        if next_run < timezone.now():
            raise BackupDocumentDataHealthCheckException("Backup not run today")

        # If we manage to get here we know that the task was run recently and
        # now we need to check to make sure that our backed up files match those
        # that are in the main documents.
        backed_up_s3_keys = DocumentData.objects.values_list("s3_key", flat=True)
        not_backed_up = Document.objects.filter(
            created_at__lte=latest_backup_log.ended_at,
            safe=True,
        ).exclude(s3_key__in=backed_up_s3_keys)
        if not_backed_up.exists():
            raise BackupDocumentDataHealthCheckException(f"{(not_backed_up.count())} files missing from backup")

    def identifier(self):  # pragma: no cover
        return self.__class__.__name__
