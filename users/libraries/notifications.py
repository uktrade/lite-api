from django.db.models import Count

from users.models import ExporterNotification, ExporterUser
from cases.models import Case


def get_exporter_user_notification_total_count(exporter_user: ExporterUser, case: Case) -> dict:
    exporter_user_notification_total_count = {}

    if exporter_user:
        exporter_user_notification_total_count["total"] = ExporterNotification.objects.filter(
            user=exporter_user, organisation=exporter_user.organisation, case=case
        ).count()

    return exporter_user_notification_total_count


def get_exporter_user_notification_individual_count(exporter_user: ExporterUser, case: Case) -> dict:
    exporter_user_notification_individual_count = {}

    if exporter_user:
        # Group by content_type (casenote, ecjuquery, generatedcasedocument).
        # Get the total number of notifications for each type
        queryset = (
            ExporterNotification.objects.filter(user=exporter_user, organisation=exporter_user.organisation, case=case)
            .values("content_type__model")
            .annotate(count=Count("content_type__model"))
        )

        # Set the model name as the key and the count as the value E.G. {"casenote": 12, "ecjuquery": 3}
        exporter_user_notification_individual_count = {
            content_type["content_type__model"]: content_type["count"] for content_type in queryset
        }

    return exporter_user_notification_individual_count
