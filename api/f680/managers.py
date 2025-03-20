from django.db import models


class F680ApplicationQuerySet(models.QuerySet):
    def get_prepared_object(self, pk):
        return self.prefetch_related(
            "security_release_requests",
            "security_release_requests__product",
            "security_release_requests__recipient",
            "security_release_requests__recipient__country",
        ).get(pk=pk)
