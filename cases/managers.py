from typing import List

from django.db import models

from cases.helpers import get_updated_case_ids, get_assigned_to_user_case_ids, get_assigned_as_case_officer_case_ids
from queues.constants import (
    ALL_CASES_QUEUE_ID,
    MY_TEAMS_QUEUES_CASES_ID,
    OPEN_CASES_QUEUE_ID,
    UPDATED_CASES_QUEUE_ID,
)
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class CaseQuerySet(models.QuerySet):
    """
    Custom queryset for the Case model. This allows us to chain application specific
    filtering logic in a reusable way.

    For example:

    To get all open cases within a specific queue:
       > qs = Case.objects.is_open().in_queue('0001')
    """

    def is_open(self, is_open: bool = True):
        func = self.exclude if is_open else self.filter
        return func(status__status__in=[CaseStatusEnum.WITHDRAWN, CaseStatusEnum.FINALISED,])

    def in_queues(self, queues: List):
        return self.filter(queues__in=queues)

    def in_queue(self, queue_id):
        return self.filter(queues__in=[queue_id])

    def in_team(self, team):
        return self.filter(queues__team=team).distinct()

    def is_updated(self, user):
        """
        Get the cases that have raised notifications when updated by an exporter
        """
        updated_case_ids = get_updated_case_ids(user)
        return self.filter(id__in=updated_case_ids)

    def assigned_to_user(self, user):
        assigned_to_user_case_ids = get_assigned_to_user_case_ids(user)
        return self.filter(id__in=assigned_to_user_case_ids)

    def assigned_as_case_officer(self, user):
        assigned_as_case_officer_case_ids = get_assigned_as_case_officer_case_ids(user)
        return self.filter(id__in=assigned_as_case_officer_case_ids)

    def has_status(self, status):
        return self.filter(status__status=status)

    def is_type(self, case_type):
        return self.filter(type=case_type)

    def order_by_status(self, order=""):
        """
        :param order: ('', '-')
        :return:
        """
        order = order if order in ["", "-"] else ""

        return self.order_by(f"{order}status__priority")

    def order_by_date(self, order=""):
        """
        :param order: ('', '-')
        :return:
        """
        order = order if order in ["", "-"] else ""

        return self.order_by(f"{order}submitted_at")


class CaseManager(models.Manager):
    """
    Custom manager for the Case model that uses CaseQuerySet and provides a reusable search
    functionality to the Case model.
    """

    def get_queryset(self):
        return CaseQuerySet(self.model, using=self.db)

    def search(
        self, queue_id=None, user=None, status=None, case_type=None, sort=None, date_order=None,
    ):
        """
        Search for a user's available cases given a set of search parameters.
        """
        case_qs = self.submitted().prefetch_related("queues", "status", "organisation__flags",)

        if queue_id == MY_TEAMS_QUEUES_CASES_ID:
            case_qs = case_qs.in_team(team=user.team)
        elif queue_id == OPEN_CASES_QUEUE_ID:
            case_qs = case_qs.is_open()
        elif queue_id == UPDATED_CASES_QUEUE_ID:
            case_qs = case_qs.is_updated(user=user)
        elif queue_id is not None and queue_id != ALL_CASES_QUEUE_ID:
            case_qs = case_qs.in_queue(queue_id=queue_id)

        if status:
            case_qs = case_qs.has_status(status=status)

        if case_type:
            case_qs = case_qs.is_type(case_type=case_type)

        if isinstance(date_order, str):
            case_qs = case_qs.order_by_date(date_order)

        if isinstance(sort, str):
            case_qs = case_qs.order_by_status(order="-" if sort.startswith("-") else "")

        return case_qs

    def submitted(self):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return self.get_queryset().exclude(status=draft)

    def get_application(self, case):
        from applications.models import StandardApplication

        try:
            return StandardApplication.objects.get(baseapplication_ptr__case_ptr=case)
        except StandardApplication.DoesNotExist:
            pass

        from applications.models import OpenApplication

        try:
            return OpenApplication.objects.get(baseapplication_ptr__case_ptr=case)
        except OpenApplication.DoesNotExist:
            pass

        raise Exception(f"Application object not found from case: {case}")

    def get_query(self, case):
        from queries.control_list_classifications.models import ControlListClassificationQuery

        try:
            return ControlListClassificationQuery.objects.get(query_ptr__case_ptr=case)
        except ControlListClassificationQuery.DoesNotExist:
            pass

        from queries.end_user_advisories.models import EndUserAdvisoryQuery

        try:
            return EndUserAdvisoryQuery.objects.get(query_ptr__case_ptr=case)
        except EndUserAdvisoryQuery.DoesNotExist:
            pass

        raise Exception(f"Query object not found from case: {case}")

    def get_obj(self, case):
        application = self.get_application(case)
        if application:
            return application

        query = self.get_query(case)
        if query:
            return query

        return case
