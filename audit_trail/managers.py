from actstream.gfk import GFKQuerySet, GFKManager



class AuditQuerySet(GFKQuerySet):
    pass
    # def delete(self):
    #     raise NotImplementedError('Delete not allowed for Audit trail.')


class AuditManager(GFKManager):
    def get_query_set(self):
        return AuditQuerySet(self.model)
    get_queryset = get_query_set
    #
    # def delete(self):
    #     raise NotImplementedError('Delete not allowed for Audit trail.')

    def create(self, *args, **kwargs):
        # TODO: decouple notifications and audit (signals?)
        audit = super(AuditManager, self).create(*args, **kwargs)
        from users.models import ExporterUser
        from users.models import GovUser
        if isinstance(kwargs.get('actor'), ExporterUser):
            for gov_user in GovUser.objects.all():
                gov_user.send_notification(audit=audit)

        return audit
