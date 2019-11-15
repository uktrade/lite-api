from random import randint

import reversion
from django.db import models

from organisations.models import Organisation
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from static.statuses.models import CaseStatus


class QueryManager(models.Manager):
    def create(self, **obj_data):
        from queries.end_user_advisories.models import EndUserAdvisoryQuery
        from cases.enums import CaseType
        from cases.models import Case

        query = super().create(
            **obj_data, status=get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        )

        # Create a case with this query
        case_type = (
            CaseType.END_USER_ADVISORY_QUERY
            if isinstance(query, EndUserAdvisoryQuery)
            else CaseType.CLC_QUERY
        )
        case = Case(query=query, type=case_type)
        case.save()

        return query


@reversion.register()
class Query(models.Model):
    """
    Base query class
    """

    id = models.BigAutoField(primary_key=True)
    submitted_at = models.DateTimeField(auto_now_add=True, blank=True)
    status = models.ForeignKey(
        CaseStatus,
        related_name="query_status",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-submitted_at"]

    # pylint: disable=W0221
    def save(self, **kwargs):
        if not self.pk:
            is_unique = False
            while not is_unique:
                pk = randint(1000000000, 1999999999)  # nosec
                is_unique = Query.objects.filter(id=pk).count() == 0
            self.pk = pk
        super(Query, self).save()

    objects = QueryManager()
