from static.statuses.models import CaseStatusOnType


def check_status_is_applicable_for_a_case_type(status, case_type):
    applicable_case_types = CaseStatusOnType.objects.filter(status=status).values_list('type', flat=True)
    return case_type in applicable_case_types
