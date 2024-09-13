from contextlib import contextmanager

from django.db import transaction

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType


@contextmanager
def developer_intervention(*, dry_run=True):
    logs = []

    def audit_log(target, message, additional_payload=None):
        if not additional_payload:
            additional_payload = {}

        audit_trail_service.create_system_user_audit(
            verb=AuditType.DEVELOPER_INTERVENTION,
            target=target,
            payload={
                "additional_text": message,
                **additional_payload,
            },
        )
        logs.append((target, message))

    with transaction.atomic():
        yield audit_log

        if not logs:
            raise ValueError("Expected at least one audit event to be logged")

        if dry_run:
            transaction.set_rollback(True)
