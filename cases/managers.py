from datetime import datetime
from typing import List

from compat import get_model
from django.db import models
from django.db.models import Q

from cases.helpers import get_updated_case_ids, get_assigned_to_user_case_ids, get_assigned_as_case_officer_case_ids
from queues.constants import (
    ALL_CASES_QUEUE_ID,
    MY_TEAMS_QUEUES_CASES_ID,
    OPEN_CASES_QUEUE_ID,
    UPDATED_CASES_QUEUE_ID,
    MY_ASSIGNED_CASES_QUEUE_ID,
    MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID,
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

    def is_open(self):
        return self.filter(status__is_terminal=False)

    def in_queues(self, queues: List):
        return self.filter(queues__in=queues)

    def in_queue(self, queue_id):
        return self.filter(queues__in=[queue_id])

    def in_team(self, team_id):
        return self.filter(queues__team_id=team_id).distinct()

    def is_updated(self, user):
        """
        Get the cases that have raised notifications when updated by an exporter
        """
        updated_case_ids = get_updated_case_ids(user)
        return self.filter(id__in=updated_case_ids)

    def assigned_to_user(self, user):
        assigned_to_user_case_ids = get_assigned_to_user_case_ids(user)
        return self.filter(id__in=assigned_to_user_case_ids)

    def not_assigned_to_any_user(self):
        return self.filter(case_assignments=None)

    def assigned_as_case_officer(self, user):
        assigned_as_case_officer_case_ids = get_assigned_as_case_officer_case_ids(user)
        return self.filter(id__in=assigned_as_case_officer_case_ids)

    def not_terminal(self):
        return self.filter(status__is_terminal=False)

    def has_status(self, status):
        return self.filter(status__status=status)

    def is_type(self, case_type):
        return self.filter(case_type=case_type)

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

    def filter_based_on_queue(self, queue_id, team_id, user):
        if queue_id == MY_TEAMS_QUEUES_CASES_ID:
            return self.in_team(team_id=team_id)
        elif queue_id == OPEN_CASES_QUEUE_ID:
            return self.is_open()
        elif queue_id == UPDATED_CASES_QUEUE_ID:
            return self.is_updated(user=user)
        elif queue_id == MY_ASSIGNED_CASES_QUEUE_ID:
            return self.assigned_to_user(user=user).not_terminal()
        elif queue_id == MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID:
            return self.assigned_as_case_officer(user=user).not_terminal()
        elif queue_id is not None and queue_id != ALL_CASES_QUEUE_ID:
            return self.in_queue(queue_id=queue_id)

        return self


class CaseManager(models.Manager):
    """
    Custom manager for the Case model that uses CaseQuerySet and provides a reusable search
    functionality to the Case model.
    """

    NOT_ASSIGNED = "not_assigned"

    def get_queryset(self):
        return CaseQuerySet(self.model, using=self.db)

    def search(
        self,
        queue_id=None,
        user=None,
        status=None,
        case_type=None,
        sort=None,
        assigned_user=None,
        case_officer=None,
        date_order=None,
        include_hidden=None,
    ):
        """
        Search for a user's available cases given a set of search parameters.
        """
        case_qs = (
            self.submitted()
            .select_related("organisation", "status")
            .prefetch_related(
                "queues",
                "case_assignments",
                "case_assignments__user",
                "case_ecju_query",
                "case_assignments__queue",
                "organisation__flags",
                "case_type",
                "flags",
            )
        )
        team_id = user.team.id

        if not include_hidden:
            EcjuQuery = get_model("cases", "ecjuquery")

            case_qs = case_qs.exclude(
                id__in=EcjuQuery.objects.filter(raised_by_user__team_id=team_id, responded_at__isnull=True)
                .values("case_id")
                .distinct()
            )

        if queue_id:
            case_qs = case_qs.filter_based_on_queue(queue_id=queue_id, team_id=team_id, user=user)

        if status:
            case_qs = case_qs.has_status(status=status)

        if case_type:
            case_qs = case_qs.is_type(case_type=case_type)

        if assigned_user:
            if assigned_user == self.NOT_ASSIGNED:
                case_qs = case_qs.not_assigned_to_any_user()
            else:
                case_qs = case_qs.assigned_to_user(user=assigned_user)

        if case_officer:
            if case_officer == self.NOT_ASSIGNED:
                case_officer = None
            case_qs = case_qs.assigned_as_case_officer(user=case_officer)

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
        from queries.goods_query.models import GoodsQuery

        try:
            return GoodsQuery.objects.get(query_ptr__case_ptr=case)
        except GoodsQuery.DoesNotExist:
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


class CaseReferenceCodeManager(models.Manager):
    def create(self):
        CaseReferenceCode = self.model
        year = datetime.now().year
        case_reference_code, _ = CaseReferenceCode.objects.get_or_create(defaults={"year": year, "reference_number": 0})

        if case_reference_code.year != year:
            case_reference_code.year = year
            case_reference_code.reference_number = 1
        else:
            case_reference_code.reference_number += 1

        case_reference_code.save()
        return case_reference_code


class AdviceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related(*self.model.ENTITY_FIELDS)

    def get(self, *args, **kwargs):
        entity_id = kwargs.pop("entity_id", None)

        if entity_id:
            query = Q()

            for entity in self.model.ENTITY_FIELDS:
                query.add(Q(**{entity: entity_id}), Q.OR)

            return super().filter(query).get(*args, **kwargs)

        return super().get(*args, **kwargs)
