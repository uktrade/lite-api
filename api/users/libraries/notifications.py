from django.db.models import Count

from cases.models import Case
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.users.models import ExporterNotification, ExporterUser


def get_exporter_user_notification_total_count(exporter_user: ExporterUser, organisation_id, case: Case) -> dict:
    return {
        "total": ExporterNotification.objects.filter(
            user=exporter_user, organisation_id=organisation_id, case=case
        ).count()
    }


def get_case_notifications(data, request):
    ids = [item["id"] for item in data]
    notifications = (
        ExporterNotification.objects.filter(
            user=request.user, organisation_id=get_request_user_organisation_id(request), case__id__in=ids
        )
        .values("case")
        .annotate(count=Count("case"))
    )
    cases_with_notifications = {str(notification["case"]): notification["count"] for notification in notifications}

    for item in data:
        if item["id"] in cases_with_notifications:
            item["exporter_user_notification_count"] = cases_with_notifications[item["id"]]
        else:
            item["exporter_user_notification_count"] = 0

    return data


def get_compliance_site_case_notifications(data, request):
    """
    returns the count of notification for a compliance site case and all visit cases under it.
    """
    ids = [item["id"] for item in data]

    notifications = (
        ExporterNotification.objects.filter(
            user=request.user, organisation_id=get_request_user_organisation_id(request), case_id__in=ids
        )
        .values("case")
        .annotate(count=Count("case"))
    )
    cases_with_notifications = {str(notification["case"]): notification["count"] for notification in notifications}

    visit_notifications = list(
        ExporterNotification.objects.filter(
            user=request.user,
            organisation_id=get_request_user_organisation_id(request),
            case__compliancevisitcase__site_case__id__in=ids,
        )
        .values("case__compliancevisitcase__site_case_id")
        .annotate(count=Count("case__compliancevisitcase__site_case_id"))
    )
    visit_cases_with_notifications = {
        str(notification["case__compliancevisitcase__site_case_id"]): notification["count"]
        for notification in visit_notifications
    }

    for item in data:
        if item["id"] in cases_with_notifications:
            item["exporter_user_notification_count"] = cases_with_notifications[item["id"]]
        else:
            item["exporter_user_notification_count"] = 0

        if item["id"] in visit_cases_with_notifications:
            item["exporter_user_notification_count"] += visit_cases_with_notifications[item["id"]]

    return data


def get_exporter_user_notification_individual_count(exporter_user: ExporterUser, organisation_id, case: Case) -> dict:
    # Group by content_type (casenote, ecjuquery, generatedcasedocument).
    # Get the total number of notifications for each type
    queryset = (
        ExporterNotification.objects.filter(user=exporter_user, organisation_id=organisation_id, case=case)
        .values("content_type__model")
        .annotate(count=Count("content_type__model"))
    )

    # Set the model name as the key and the count as the value E.G. {"casenote": 12, "ecjuquery": 3}
    return {content_type["content_type__model"]: content_type["count"] for content_type in queryset}


def get_exporter_user_notification_individual_count_with_compliance_visit(
    exporter_user: ExporterUser, organisation_id, case: Case
) -> dict:
    # Group by content_type (casenote, ecjuquery, generatedcasedocument, visitreport).
    # Get the total number of notifications for each type
    data = get_exporter_user_notification_individual_count(exporter_user, organisation_id, case)
    data["visitreport"] = ExporterNotification.objects.filter(
        user=exporter_user, organisation_id=organisation_id, case__compliancevisitcase__site_case=case
    ).count()
    return data
