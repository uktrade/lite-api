from django.db import models


class F680ApplicationQuerySet(models.QuerySet):
    def get_prepared_object(self, pk):
        return self.get(pk=pk)
