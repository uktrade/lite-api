from actstream.gfk import GFKQuerySet, GFKManager


class AuditQuerySet(GFKQuerySet):
    def delete(self):
        print('\n\n[QUERYSET] ATTEMPTING DELETE')


class AuditManager(GFKManager):
    def get_query_set(self):
        return AuditQuerySet(self.model)
    get_queryset = get_query_set

    def none(self):
        return self.get_queryset().none()

    def delete(self):
        print('\n\n[MODEL] ATTEMPTING DELETE')
