from django.db.models import Count

from users.models import ExporterNotification, ExporterUser
from cases.models import Case


def get_exporter_user_notification_total_count(exporter_user: ExporterUser, case: Case) -> dict:
    return {
        "total": ExporterNotification.objects.filter(
            user=exporter_user, organisation=exporter_user.organisation, case=case
        ).count()
    }


def get_exporter_user_notification_individual_count(exporter_user: ExporterUser, case: Case) -> dict:
    # Group by content_type (casenote, ecjuquery, generatedcasedocument).
    # Get the total number of notifications for each type
    queryset = (
        ExporterNotification.objects.filter(user=exporter_user, organisation=exporter_user.organisation, case=case)
        .values("content_type__model")
        .annotate(count=Count("content_type__model"))
    )

    # Set the model name as the key and the count as the value E.G. {"casenote": 12, "ecjuquery": 3}
    return {content_type["content_type__model"]: content_type["count"] for content_type in queryset}
