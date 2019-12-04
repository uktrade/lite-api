from audit_trail import service as audit_service
from audit_trail.constants import Verb
from cases.libraries.activity_types import CaseActivityType
from cases.models import CaseActivity, Case


def _get_case_from_application(application):
    try:
        return application.case.get()
    except Case.DoesNotExist:
        return None


def set_case_activity(user, verb, application, payload):
    case = _get_case_from_application(application)

    if case:
        audit_service.create(
            actor=user,
            verb=verb,
            target=case,
            payload=payload
        )


def set_application_ref_number_case_activity(old_ref_number, new_ref_number, user, application):
    payload = {
        "old_ref_number": old_ref_number,
        "new_ref_number": new_ref_number,
    }

    set_case_activity(user, Verb.UPDATED_APPLICATION, application, payload)


def set_application_status_case_activity(status, user, application):
    payload = {
        "status": status,
    }

    set_case_activity(user, Verb.UPDATED_STATUS, application, payload)


def set_site_case_activity(removed_locations, removed_sites, new_sites, user, application):
    case_activities = []

    if removed_locations:
        case_activity_removed_locations = [
            location.external_location.name + " " + location.external_location.country.name
            for location in removed_locations
        ]

        case_activities.append(
            {
                "activity_type": CaseActivityType.REMOVED_EXTERNAL_LOCATIONS_FROM_APPLICATION,
                "locations": case_activity_removed_locations,
            }
        )

    if removed_sites:
        case_activity_removed_sites = [site.site.name + " " + site.site.address.country.name for site in removed_sites]

        case_activities.append(
            {"activity_type": CaseActivityType.REMOVED_SITES_FROM_APPLICATION, "sites": case_activity_removed_sites,}
        )

    if new_sites:
        case_activity_new_sites = [site.name + " " + site.address.country.name for site in new_sites]
        case_activities.append(
            {"activity_type": CaseActivityType.ADD_SITES_TO_APPLICATION, "sites": case_activity_new_sites,}
        )

    for case_activity in case_activities:
        set_case_activity(case_activity, user, application)


def set_external_location_case_activity(removed_sites, removed_locations, new_locations, user, application):
    case_activities = []

    if removed_sites:
        case_activity_removed_sites = [site.site.name + " " + site.site.address.country.name for site in removed_sites]

        case_activities.append(
            {"activity_type": CaseActivityType.REMOVED_SITES_FROM_APPLICATION, "sites": case_activity_removed_sites,}
        )

    if removed_locations:
        case_activity_removed_locations = [
            location.external_location.name + " " + location.external_location.country.name
            for location in removed_locations
        ]

        case_activities.append(
            {
                "activity_type": CaseActivityType.REMOVED_EXTERNAL_LOCATIONS_FROM_APPLICATION,
                "locations": case_activity_removed_locations,
            }
        )

    if new_locations:
        case_activity_new_locations = [location.name + " " + location.country.name for location in new_locations]

        case_activities.append(
            {
                "activity_type": CaseActivityType.ADD_EXTERNAL_LOCATIONS_TO_APPLICATION,
                "locations": case_activity_new_locations,
            }
        )

    for case_activity in case_activities:
        set_case_activity(case_activity, user, application)


def set_countries_case_activity(removed_countries, new_countries, user, application):
    case_activities = []

    if removed_countries:
        case_activity_removed_countries = [country.country.name for country in removed_countries]
        case_activities.append(
            {
                "activity_type": CaseActivityType.REMOVED_COUNTRIES_FROM_APPLICATION,
                "countries": case_activity_removed_countries,
            }
        )

    if new_countries:
        case_activity_new_countries = [country.name for country in new_countries]

        case_activities.append(
            {"activity_type": CaseActivityType.ADD_COUNTRIES_TO_APPLICATION, "countries": case_activity_new_countries,}
        )

    for case_activity in case_activities:
        set_case_activity(case_activity, user, application)


def set_party_case_activity(activity_type, party_type, party_name, user, application):
    case_activity = {
        "activity_type": activity_type,
        "party_type": party_type.replace("_", " "),
        "party_name": party_name,
    }

    set_case_activity(case_activity, user, application)


def set_application_goods_case_activity(activity_type, good_name, user, application):
    case_activity = {"activity_type": activity_type, "good_name": good_name}

    set_case_activity(case_activity, user, application)


def set_application_goods_type_case_activity(activity_type, good_type_name, user, application):
    case_activity = {"activity_type": activity_type, "good_type_name": good_type_name}

    set_case_activity(case_activity, user, application)


def set_application_document_case_activity(activity_type, file_name, user, application):
    case_activity = {"activity_type": activity_type, "file_name": file_name}

    set_case_activity(case_activity, user, application)


def set_party_document_case_activity(activity_type, file_name, party_type, party_name, user, application):
    case_activity = {
        "activity_type": activity_type,
        "file_name": file_name,
        "party_type": party_type.replace("_", " "),
        "party_name": party_name,
    }

    set_case_activity(case_activity, user, application)
