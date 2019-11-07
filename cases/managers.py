from typing import List

from django.db import models
from django.db.models import Q
from django.db.models.functions import Coalesce

from queues.constants import ALL_CASES_SYSTEM_QUEUE_ID, MY_TEAMS_QUEUES_CASES_ID, OPEN_CASES_SYSTEM_QUEUE_ID
from static.statuses.enums import CaseStatusEnum


class CaseQuerySet(models.QuerySet):
    def is_open(self, is_open: bool = True):
        func = self.exclude if is_open else self.filter
        return func(
            Q(application__status__status__in=[CaseStatusEnum.WITHDRAWN, CaseStatusEnum.FINALISED]) |
            Q(query__status__status__in=[CaseStatusEnum.WITHDRAWN, CaseStatusEnum.FINALISED])
        )

    def in_queues(self, queues: List):
        return self.filter(queues__in=queues)

    def in_queue(self, queue_id):
        return self.filter(queues__in=[queue_id])

    def in_team(self, team):
        return self.filter(queues__team=team).distinct()

    def has_status(self, status):
        return self.filter(Q(query__status__status=status) | Q(application__status__status=status))

    def is_type(self, case_type):
        return self.filter(type=case_type)

    def order_by_status(self, order=''):
        """
        :param order: ('', '-')
        :return:
        """
        order = order if order in ['', '-'] else ''

        return self.annotate(
            status__priority=Coalesce('application__status__priority', 'query__status__priority')
        ).order_by(f'{order}status__priority')

    def order_by_date(self, order=''):
        """
        :param order: ('', '-')
        :return:
        """
        order = order if order in ['', '-'] else ''

        return self.annotate(
            created_at=Coalesce('application__submitted_at', 'query__submitted_at'),
        ).order_by(f'{order}created_at')


class CaseManager(models.Manager):
    def get_queryset(self):
        return CaseQuerySet(self.model, using=self.db)

    def search(self, queue_id=None, team=None, status=None, case_type=None, sort=None, date_order=None):
        """
        Search for a user's available cases given a set of search parameters.
        """
        case_qs = self.get_queryset().prefetch_related(
            'queues',
            'query__status',
            'application__status',
            'query__organisation__flags',
            'application__organisation__flags'
        )

        if queue_id == MY_TEAMS_QUEUES_CASES_ID:
            case_qs = case_qs.in_team(team=team)

        elif queue_id == OPEN_CASES_SYSTEM_QUEUE_ID:
            case_qs = case_qs.is_open()

        elif queue_id is not None and queue_id != ALL_CASES_SYSTEM_QUEUE_ID:
            case_qs = case_qs.in_queue(queue_id=queue_id)

        if status:
            case_qs = case_qs.has_status(status=status)

        if case_type:
            case_qs = case_qs.is_type(case_type=case_type)

        if isinstance(date_order, str):
            case_qs = case_qs.order_by_date(date_order)

        if isinstance(sort, str):
            case_qs = case_qs.order_by_status(order='-' if sort.startswith('-') else '')

        return case_qs
