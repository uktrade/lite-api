from cases.libraries.activity_types import CaseActivityType
from cases.models import CaseActivity, Case


def _get_case_from_application(application):
    try:
        return application.case.get()
    except Case.DoesNotExist:
        return None


def set_case_activity(case_activity, user, application):
    case = _get_case_from_application(application)

    if case:
        CaseActivity.create(case=case, user=user, **case_activity)


def set_application_name_case_activity(old_name, new_name, user, application):
    case_activity = {
        'activity_type': CaseActivityType.UPDATED_APPLICATION_NAME,
        'old_name': old_name,
        'new_name': new_name
    }

    set_case_activity(case_activity, user, application)


def set_application_ref_number_case_activity(old_ref_number, new_ref_number, user, application):
    case_activity = {
        'activity_type': CaseActivityType.UPDATED_APPLICATION_REFERENCE_NUMBER,
        'old_ref_number': old_ref_number,
        'new_ref_number': new_ref_number
    }

    set_case_activity(case_activity, user, application)


def set_application_status_case_activity(status, user, application):
    case_activity = {
        'activity_type': CaseActivityType.UPDATED_STATUS,
        'status': status,
    }

    set_case_activity(case_activity, user, application)


def set_site_case_activity(deleted_external_location_count, deleted_site_count, new_sites, user, application):
    case_activities = []

    if deleted_external_location_count:
        case_activities.append({
            'activity_type': CaseActivityType.DELETE_ALL_EXTERNAL_LOCATIONS_FROM_APPLICATION
        })

    if deleted_site_count:
        case_activities.append({
            'activity_type': CaseActivityType.DELETE_ALL_SITES_FROM_APPLICATION
        })

    case_activity_sites = [site.name + ' ' +
                           site.address.country.name
                           for site in new_sites]

    case_activities.append({
        'activity_type': CaseActivityType.ADD_SITES_TO_APPLICATION,
        'sites': case_activity_sites
    })

    for case_activity in case_activities:
        set_case_activity(case_activity, user, application)


def set_external_location_case_activity(deleted_site_count, deleted_external_location_count, new_external_locations,
                                        user, application):
    case_activities = []

    if deleted_site_count:
        case_activities.append({
            'activity_type': CaseActivityType.DELETE_ALL_SITES_FROM_APPLICATION
        })

    if deleted_external_location_count:
        case_activities.append({
            'activity_type': CaseActivityType.DELETE_ALL_EXTERNAL_LOCATIONS_FROM_APPLICATION
        })

    case_activity_locations = [external_location.name + ' ' +
                               external_location.country.name
                               for external_location in new_external_locations]

    case_activities.append({
        'activity_type': CaseActivityType.ADD_EXTERNAL_LOCATIONS_TO_APPLICATION,
        'locations': case_activity_locations
    })

    for case_activity in case_activities:
        set_case_activity(case_activity, user, application)


def set_countries_case_activity(deleted_country_count, new_countries, user, application):
    case_activities = []

    if deleted_country_count:
        case_activities.append({
            'activity_type': CaseActivityType.DELETE_ALL_COUNTRIES_FROM_APPLICATION
        })

    case_activity_countries = [country.name for country in new_countries]

    case_activities.append({
        'activity_type': CaseActivityType.ADD_COUNTRIES_TO_APPLICATION,
        'countries': case_activity_countries
    })

    for case_activity in case_activities:
        set_case_activity(case_activity, user, application)


def set_party_case_activity(activity_type, party_type, party_name, user, application):
    case_activity = {
        'activity_type': activity_type,
        'party_type': party_type.replace("_", " "),
        'party_name': party_name
    }

    set_case_activity(case_activity, user, application)


def set_application_goods_case_activity(activity_type, good_name, user, application):
    case_activity = {
        'activity_type': activity_type,
        'good_name': good_name
    }

    set_case_activity(case_activity, user, application)


def set_application_document_case_activity(activity_type, file_name, user, application):
    case_activity = {
        'activity_type': activity_type,
        'file_name': file_name
    }

    set_case_activity(case_activity, user, application)


def set_party_document_case_activity(activity_type, file_name, party_type, party_name, user, application):
    case_activity = {
        'activity_type': activity_type,
        'file_name': file_name,
        'party_type': party_type.replace("_", " "),
        'party_name': party_name,
    }

    set_case_activity(case_activity, user, application)
