from django.db.models import Count, F

from api.applications.models import StandardApplication
from api.cases.models import Case
from api.goods.models import FirearmGoodDetails
from api.organisations.libraries.get_organisation import get_request_user_organisation, get_request_user_organisation_id
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.models import ExporterNotification, ExporterUser


def get_exporter_user_notification_total_count(exporter_user: ExporterUser, organisation_id, case: Case) -> dict:
    return {
        "total": ExporterNotification.objects.filter(
            user_id=exporter_user.pk, organisation_id=organisation_id, case=case
        ).count()
    }


def get_cases_with_missing_serials(request):
    applications = StandardApplication.objects.filter(
        organisation=get_request_user_organisation(request)
    ).prefetch_related("goods__firearm_details")
    applications = applications.filter(
        status__in=[
            get_case_status_by_status(CaseStatusEnum.SUBMITTED),
            get_case_status_by_status(CaseStatusEnum.FINALISED),
        ]
    )
    applications = applications.filter(
        goods__firearm_details__serial_numbers_available__in=FirearmGoodDetails.SerialNumberAvailability.get_has_serial_numbers_values(),
        goods__firearm_details__serial_numbers__len__lt=F("goods__firearm_details__number_of_items"),
    )
    return applications


def get_case_notifications(data, request):
    ids = [item["id"] for item in data]
    notifications = (
        ExporterNotification.objects.filter(
            user_id=request.user.pk, organisation_id=get_request_user_organisation_id(request), case__id__in=ids
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

    # add missing serial number cases to notifications
    applications = get_cases_with_missing_serials(request)
    cases_with_missing_serials = {application.reference_code: 1 for application in applications}

    for item in data:
        if item["reference_code"] in cases_with_missing_serials:
            item["exporter_user_notification_count"] += cases_with_missing_serials[item["reference_code"]]

    return data


def get_compliance_site_case_notifications(data, request):
    """
    returns the count of notification for a compliance site case and all visit cases under it.
    """
    ids = [item["id"] for item in data]

    notifications = (
        ExporterNotification.objects.filter(
            user_id=request.user.pk, organisation_id=get_request_user_organisation_id(request), case_id__in=ids
        )
        .values("case")
        .annotate(count=Count("case"))
    )
    cases_with_notifications = {str(notification["case"]): notification["count"] for notification in notifications}

    visit_notifications = list(
        ExporterNotification.objects.filter(
            user_id=request.user.pk,
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
        ExporterNotification.objects.filter(user_id=exporter_user.pk, organisation_id=organisation_id, case=case)
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
        user_id=exporter_user.pk, organisation_id=organisation_id, case__compliancevisitcase__site_case=case
    ).count()
    return data
