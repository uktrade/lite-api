from cases.models import Case, CaseActivity


def set_party_case_activity(application_id, user, party_type, party_name, activity_type):
    try:
        case = Case.objects.get(application__id=application_id)
    except Case.DoesNotExist:
        return

    CaseActivity.create(activity_type=activity_type,
                        case=case,
                        user=user,
                        party_type=party_type,
                        party_name=party_name)
