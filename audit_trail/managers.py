from actstream.gfk import GFKQuerySet, GFKManager

from static.statuses.enums import CaseStatusEnum
from users.models import ExporterUser
from users.models import GovUser


class AuditQuerySet(GFKQuerySet):
    pass


class AuditManager(GFKManager):
    def get_query_set(self):
        return AuditQuerySet(self.model)

    get_queryset = get_query_set

    def create(self, *args, **kwargs):
        # TODO: decouple notifications and audit (signals?)
        from cases.models import Case

        target = kwargs.get("target")

        if isinstance(target, Case):
            # Only audit cases if they do not have status set to 'draft'
            if target.status.status != CaseStatusEnum.DRAFT:
                audit = super(AuditManager, self).create(*args, **kwargs)
                actor = kwargs.get("actor")

                if isinstance(actor, ExporterUser):
                    # Notify gov users when exporter updates a case
                    for gov_user in GovUser.objects.all():
                        gov_user.send_notification(content_object=audit, case=target)

                return audit

            return None

        return super(AuditManager, self).create(*args, **kwargs)
