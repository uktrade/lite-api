from typing import List
from actstream.gfk import GFKQuerySet, GFKManager
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, OuterRef

from api.cases.models import Case
from api.staticdata.statuses.libraries.case_status_validate import is_case_status_draft
from api.users.models import ExporterUser
from api.users.models import GovUser


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
        actor: the object causing the audit entry (such as a user)
        send_notification: certain scenarios alert internal users, default is True
        ignore_case_status: draft cases become audited, default is False
        """
        # TODO: decouple notifications and audit (signals?)
        target = kwargs.get("target")
        actor = kwargs.get("actor")
        send_notification = kwargs.pop("send_notification", True)
        ignore_case_status = kwargs.pop("ignore_case_status", False)

        if isinstance(target, Case):
            # Only audit cases if their status is not draft
            if not is_case_status_draft(target.status.status) or ignore_case_status:
                audit = super(AuditManager, self).create(*args, **kwargs)

                # Notify gov users when an exporter updates a case
                if isinstance(actor, ExporterUser) and send_notification:
                    for gov_user in GovUser.objects.all():
                        gov_user.send_notification(content_object=audit, case=target)

                return audit

            return None

        return super(AuditManager, self).create(*args, **kwargs)

    def get_latest_activities(self, case_ids: List, number_of_results):
        obj_type = ContentType.objects.get_for_model(Case)
        top_x_per_case = (
            self.get_queryset()
            .filter(
                Q(action_object_object_id=OuterRef("action_object_object_id"), action_object_content_type=obj_type)
                | Q(target_object_id=OuterRef("target_object_id"), target_content_type=obj_type)
            )
            .order_by("-updated_at")
        )
        if number_of_results > 1:
            # iterate over audit records once and add max of 'number_of_results' matching
            # action_object_content_type or target_content_type (up to 2x'number_of_results' total)
            top_x_per_case[:number_of_results]
        return self.get_queryset().filter(
            Q(id__in=top_x_per_case.values("id")),
            Q(target_object_id__in=case_ids, target_content_type=obj_type)
            | Q(action_object_object_id__in=case_ids, action_object_content_type=obj_type),
        )
