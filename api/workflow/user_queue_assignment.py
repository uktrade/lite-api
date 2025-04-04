from django.utils import timezone

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType

from api.cases.enums import ApplicationFeatures
from api.cases.models import Case, CaseQueueMovement
from api.compliance.helpers import compliance_visit_case_complete
from api.compliance.models import ComplianceVisitCase
from api.queues.models import Queue
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.users.enums import SystemUser
from api.users.models import BaseUser

from lite_routing.routing_rules_internal.routing_engine import move_case_forward


def get_queues_with_case_assignments(case: Case):
    return set(Queue.objects.filter(case_assignments__case=case).distinct())


def get_next_goods_query_status(case):
    goods_query = case.query.goodsquery
    if (goods_query.clc_responded or not goods_query.clc_raised_reasons) and goods_query.pv_grading_raised_reasons:
        if goods_query.status.status != CaseStatusEnum.PV and not goods_query.status.is_terminal:
            return CaseStatus.objects.get(status=CaseStatusEnum.PV, is_terminal=False)
    return None


def get_next_compliance_visit_status(case):
    # Awaiting exporter response is the last status before a terminal status (closed) as such we must confirm that
    #   the case is ready to be closed.
    if case.status.status == CaseStatusEnum.AWAITING_EXPORTER_RESPONSE:
        comp_case = ComplianceVisitCase.objects.get(id=case.id)
        if not compliance_visit_case_complete(comp_case):
            return None
        return CaseStatus.objects.get(status=CaseStatusEnum.CLOSED)
    elif case.status.status == CaseStatusEnum.CLOSED:
        return None
    else:
        current_status_pos = CaseStatusEnum.compliance_visit_statuses.index(case.status.status)
        # The case status enum was used to get the next status as workflow automation uses some statuses in other
        #   workflows
        return CaseStatus.objects.get(status=CaseStatusEnum.compliance_visit_statuses[current_status_pos + 1])


# This here allows us to look at each queue removed, and assign a countersigning queue for the work queue as needed
def assign_to_countersign_queues(case, queues_without_case_assignments):
    system_user = BaseUser.objects.get(id=SystemUser.id)
    for queue in queues_without_case_assignments:
        if queue.countersigning_queue_id:
            remaining_feeder_queues = case.queues.filter(countersigning_queue_id=queue.countersigning_queue_id)
            if not remaining_feeder_queues:
                case.queues.add(queue.countersigning_queue_id)

                CaseQueueMovement.objects.create(case=case, queue_id=queue.countersigning_queue_id)

                # Be careful when editing this audit trail event; we depend on it for
                # the flagging rule lite_routing.routing_rules_internal.flagging_rules_criteria:mod_consolidation_required_flagging_rule_criteria()
                audit_trail_service.create(
                    actor=system_user,
                    verb=AuditType.MOVE_CASE,
                    action_object=case.get_case(),
                    payload={
                        "queues": queue.countersigning_queue.name,
                        "queue_ids": [str(queue.countersigning_queue_id)],
                        "case_status": case.status.status,
                    },
                )


def user_queue_assignment_workflow(queues: [Queue], case: Case):
    application_manifest = case.get_application_manifest()

    # Remove case from queues where all gov users are done with the case
    queues_without_case_assignments = set(queues) - get_queues_with_case_assignments(case)
    case.queues.remove(*queues_without_case_assignments)

    # Checks whether application type can require countersigning and deals accordingly
    if application_manifest.has_feature(ApplicationFeatures.ROUTE_TO_COUNTERSIGNING_QUEUES):
        assign_to_countersign_queues(case, queues_without_case_assignments)

    # Move case to next non-terminal state if unassigned from all queues
    queues_assigned = move_case_forward(case)

    created_at = timezone.now()
    for queue in queues_assigned:
        CaseQueueMovement.objects.create(case=case, queue_id=queue, created_at=created_at)
