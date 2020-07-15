from cases.enums import CaseTypeReferenceEnum
from static.statuses.enums import CaseStatusEnum
from users.models import GovUser, GovNotification


def get_assigned_to_user_case_ids(user: GovUser):
    from cases.models import CaseAssignment

    return CaseAssignment.objects.filter(user=user).values_list("case__id", flat=True)


def get_users_assigned_to_case(case_assignments):
    users = []

    for case_assignment in case_assignments:
        queue_users = [
            {"first_name": first_name, "last_name": last_name, "email": email, "queue": case_assignment.queue.name,}
            for first_name, last_name, email in case_assignment.users.values_list("first_name", "last_name", "email")
        ]

        users.extend(queue_users)
    return users


def get_assigned_as_case_officer_case_ids(user: GovUser):
    from cases.models import Case

    return Case.objects.filter(case_officer=user).values_list("id", flat=True)


def get_updated_case_ids(user: GovUser):
    """
    Get the cases that have raised notifications when updated by an exporter
    """
    assigned_to_user_case_ids = get_assigned_to_user_case_ids(user)
    assigned_as_case_officer_case_ids = get_assigned_as_case_officer_case_ids(user)
    cases = assigned_to_user_case_ids.union(assigned_as_case_officer_case_ids)

    return GovNotification.objects.filter(user=user, case__id__in=cases).values_list("case__id", flat=True)


def remove_next_review_date(case, request, pk):
    """
    Clears the next review date for that team if there are no other team members assigned to the case
    """
    from cases.models import CaseAssignment

    if case.case_review_date.exists():
        other_assigned_users = (
            CaseAssignment.objects.filter(case__id=pk, queue__team_id=request.user.team_id)
            .exclude(user=request.user)
            .exists()
        )
        if not other_assigned_users:
            case.case_review_date.filter(case__id=pk, team_id=request.user.team_id).delete()


def can_set_status(case, status):
    """
    Returns true or false depending on different case conditions
    """
    from compliance.models import ComplianceVisitCase
    from compliance.helpers import compliance_visit_case_complete

    reference_type = case.case_type.reference

    if reference_type == CaseTypeReferenceEnum.COMP_SITE and status not in CaseStatusEnum.compliance_site_statuses:
        return False
    elif reference_type == CaseTypeReferenceEnum.COMP_VISIT and status not in CaseStatusEnum.compliance_visit_statuses:
        return False

    if case.case_type.reference == CaseTypeReferenceEnum.COMP_VISIT and CaseStatusEnum.is_terminal(status):
        comp_case = ComplianceVisitCase.objects.get(id=case.id)
        if not compliance_visit_case_complete(comp_case):
            return False

    if reference_type == CaseTypeReferenceEnum.CRE and status not in [
        CaseStatusEnum.CLOSED,
        CaseStatusEnum.SUBMITTED,
        CaseStatusEnum.RESUBMITTED,
    ]:
        return False

    return True
