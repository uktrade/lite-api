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
