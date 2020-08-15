from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType

from cases.enums import CaseTypeEnum
from cases.models import Case
from api.compliance.helpers import compliance_visit_case_complete
from api.compliance.models import ComplianceVisitCase
from api.queues.models import Queue
from api.static.statuses.enums import CaseStatusEnum
from api.static.statuses.models import CaseStatus
from api.users.enums import SystemUser
from api.users.models import BaseUser


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


def get_next_status_in_workflow_sequence(case):
    if case.case_type.reference == CaseTypeEnum.GOODS.reference:
        return get_next_goods_query_status(case)
    elif case.case_type.reference == CaseTypeEnum.COMPLIANCE_VISIT.reference:
        return get_next_compliance_visit_status(case)
    elif case.case_type.reference == CaseTypeEnum.HMRC.reference:
        return None
    else:
        status = case.status
        if status.workflow_sequence:
            next_status_id = status.workflow_sequence + 1
            try:
                return CaseStatus.objects.get(workflow_sequence=next_status_id, is_terminal=False)
            except CaseStatus.DoesNotExist:
                # If case workflow does have not have a next status
                # Try/catch also verifies that multiple statuses do not exist for a given sequence ID
                pass

        return None


def user_queue_assignment_workflow(queues: [Queue], case: Case):
    from api.workflow.automation import run_routing_rules

    # Remove case from queues where all gov users are done with the case
    queues_without_case_assignments = set(queues) - get_queues_with_case_assignments(case)
    case.queues.remove(*queues_without_case_assignments)

    system_user = BaseUser.objects.get(id=SystemUser.id)

    # This here allows us to look at each queue removed, and assign a countersigning queue for the work queue as needed
    for queue in queues_without_case_assignments:
        if queue.countersigning_queue_id:
            case.queues.add(queue.countersigning_queue_id)
            audit_trail_service.create(
                actor=system_user,
                verb=AuditType.MOVE_CASE,
                action_object=case.get_case(),
                payload={"queues": queue.countersigning_queue.name},
            )

    # Move case to next non-terminal state if unassigned from all queues
    if case.queues.count() == 0:
        next_status = get_next_status_in_workflow_sequence(case)
        if next_status:
            case.status = next_status
            case.save()
            run_routing_rules(case)
