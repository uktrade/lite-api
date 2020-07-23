from actstream.gfk import GFKQuerySet, GFKManager

from static.statuses.libraries.case_status_validate import is_case_status_draft
from users.models import ExporterUser
from users.models import GovUser


class AuditQuerySet(GFKQuerySet):
    pass


class AuditManager(GFKManager):
    def get_query_set(self):
        """
        Exclude hidden audits from regular business flow
        """
        return AuditQuerySet(self.model)

    get_queryset = get_query_set

    def create(self, *args, **kwargs):
        """
        Create an audit entry for a model
        target: the target object (such as a case)
        actor: the object causing the audit entry (such as a user)
        send_notification: certain scenarios alert internal users, default is True
        ignore_case_status: draft cases become audited, default is False
        """
        # TODO: decouple notifications and audit (signals?)
        from cases.models import Case

        target = kwargs.get("target")
        actor = kwargs.get("actor")
        send_notification = kwargs.pop("send_notification", True)
        ignore_case_status = kwargs.pop("ignore_case_status", False)

        if isinstance(target, Case):
            # Only audit cases if their status is not draft
            if not is_case_status_draft(target.status.status) or ignore_case_status:
                audit = super(AuditManager, self).create(*args, **kwargs)

                # Notify gov users when an exporter updates a case
                if isinstance(actor, ExporterUser) and send_notification:
                    for gov_user in GovUser.objects.all():
                        gov_user.send_notification(content_object=audit, case=target)

                return audit

            return None

        return super(AuditManager, self).create(*args, **kwargs)
