from django.db import models
from typing import List

from django.db.models import Q

from static.statuses.enums import CaseStatusEnum


class CaseQuerySet(models.QuerySet):
    def open(self):
        return self.exclude(
            query__status__status__in=[CaseStatusEnum.WITHDRAWN, CaseStatusEnum.FINALISED],
            application__status__status=[CaseStatusEnum.WITHDRAWN, CaseStatusEnum.FINALISED]
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


class CaseManager(models.Manager):
    def get_queryset(self):
        return CaseQuerySet(self.model, using=self.db)

    def open(self):
        return self.get_queryset().open()

    def in_queues(self, queues: List):
        return self.get_queryset().in_queues(queues)

    def in_queue(self, queue_id):
        return self.get_queryset().in_queue(queue_id)

    def in_team(self, team):
        return self.get_queryset().in_team(team)

    def has_status(self, status):
        return self.get_queryset().has_status(status)

    def is_type(self, case_type):
        return self.get_queryset().is_type(case_type)
