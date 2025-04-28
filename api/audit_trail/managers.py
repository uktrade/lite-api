from typing import List
from actstream.gfk import GFKQuerySet, GFKManager
from django.contrib.contenttypes.models import ContentType
from django.db.models import (
    Case as DBCase,
    F,
    Q,
    When,
    Window,
)
from django.db.models.functions.window import RowNumber

from api.cases.models import Case
from api.staticdata.statuses.libraries.case_status_validate import is_case_status_draft


class AuditQuerySet(GFKQuerySet):
    pass


class AuditManager(GFKManager):
    def get_query_set(self):
        """
        Exclude hidden audits from regular business flow
        """
        return AuditQuerySet(self.model)

    get_queryset = get_query_set

    def create(self, *args, **kwargs):
        """
        Create an audit entry for a model
        target: the target object (such as a case)
        ignore_case_status: draft cases become audited, default is False
        """
        target = kwargs.get("target")
        ignore_case_status = kwargs.pop("ignore_case_status", False)

        if isinstance(target, Case):
            # Only audit cases if their status is not draft
            if not is_case_status_draft(target.status.status) or ignore_case_status:
                audit = super(AuditManager, self).create(*args, **kwargs)
                return audit
            return None

        return super(AuditManager, self).create(*args, **kwargs)

    def get_latest_activities(self, case_ids: List, number_of_results):
        obj_type = ContentType.objects.get_for_model(Case)

        all_activities = self.get_queryset()

        # We only care about audit records that are linked to a case, however they may be linked via either the target
        # relation or the action relation.
        # First we filter to find all of the ones that are related to a case and then simplify this down to a single
        # value for the case id relation.
        case_related_activities = all_activities.filter(
            Q(action_object_content_type=obj_type) | Q(target_content_type=obj_type)
        )
        case_related_activities = case_related_activities.annotate(
            activity_case_id=DBCase(
                When(target_content_type=obj_type, then=F("target_object_id")),
                When(action_object_content_type=obj_type, then=F("action_object_object_id")),
            )
        )
        case_related_activities = case_related_activities.filter(activity_case_id__in=case_ids)

        # We can now find the latest `n` activities using a window function.
        top_n_activities = case_related_activities.annotate(
            case_row=Window(expression=RowNumber(), partition_by=["activity_case_id"], order_by="-created_at")
        ).filter(case_row__lte=number_of_results)

        return top_n_activities.order_by("activity_case_id", "case_row")
