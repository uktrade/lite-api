from actstream.gfk import GFKQuerySet, GFKManager


class AuditQuerySet(GFKQuerySet):
    def delete(self):
        raise NotImplementedError('Delete not allowed for Audit trail.')


class AuditManager(GFKManager):
    def get_query_set(self):
        return AuditQuerySet(self.model)
    get_queryset = get_query_set

    def delete(self):
        raise NotImplementedError('Delete not allowed for Audit trail.')
