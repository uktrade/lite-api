from api.audit_trail.models import Audit
from api.flags.models import Flag


def remove_flags_on_finalisation(case):
    flags_to_remove = Flag.objects.filter(remove_on_finalised=True)
    case.flags.remove(*flags_to_remove)


def remove_flags_from_audit_trail(case):
    flags_to_remove_ids = [str(flag.id) for flag in Flag.objects.filter(remove_on_finalised=True)]
    audit_logs = Audit.objects.filter(target_object_id=case.id)

    for flag_id in flags_to_remove_ids:
        for audit_log in audit_logs:
            payload = audit_log.payload
            if flag_id in payload.get("added_flags_id", []) or flag_id in payload.get("removed_flags_id", []):
                audit_log.delete()
