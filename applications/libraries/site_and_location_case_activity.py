from cases.libraries.activity_types import CaseActivityType
from cases.models import Case, CaseActivity


def set_site_case_activity(application, user, deleted_external_location_count, deleted_site_count, new_sites):
    try:
        case = Case.objects.get(application=application)
    except Case.DoesNotExist:
        return

    if deleted_external_location_count:
        CaseActivity.create(activity_type=CaseActivityType.DELETE_ALL_EXTERNAL_LOCATIONS_FROM_APPLICATION,
                            case=case,
                            user=user)

    if deleted_site_count:
        CaseActivity.create(activity_type=CaseActivityType.DELETE_ALL_SITES_FROM_APPLICATION,
                            case=case,
                            user=user)

    case_activity_sites = [site.name + ' ' +
                           site.address.country.name
                           for site in new_sites]

    CaseActivity.create(activity_type=CaseActivityType.ADD_SITES_TO_APPLICATION,
                        case=case,
                        user=user,
                        sites=case_activity_sites)


def set_external_location_case_activity(application, user, deleted_site_count,
                                        deleted_external_location_count, new_external_locations):
    try:
        case = Case.objects.get(application=application)
    except Case.DoesNotExist:
        return

    if deleted_site_count:
        CaseActivity.create(activity_type=CaseActivityType.DELETE_ALL_SITES_FROM_APPLICATION,
                            case=case,
                            user=user)

    if deleted_external_location_count:
        CaseActivity.create(activity_type=CaseActivityType.DELETE_ALL_EXTERNAL_LOCATIONS_FROM_APPLICATION,
                            case=case,
                            user=user)

    case_activity_locations = [external_location.name + ' ' +
                               external_location.country.name
                               for external_location in new_external_locations]

    CaseActivity.create(activity_type=CaseActivityType.ADD_EXTERNAL_LOCATIONS_TO_APPLICATION,
                        case=case,
                        user=user,
                        locations=case_activity_locations)
