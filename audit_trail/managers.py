from actstream.gfk import GFKQuerySet, GFKManager

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

        audit = super(AuditManager, self).create(*args, **kwargs)

        if isinstance(kwargs.get("target"), Case) and isinstance(kwargs.get("actor"), ExporterUser):
            # Notify gov users when exporter updates a case
            for gov_user in GovUser.objects.all():
                gov_user.send_notification(audit=audit)

        return audit
