from django.db.models import Count

from users.models import ExporterNotification, ExporterUser
from cases.models import Case


def get_exporter_user_notifications_total_count(exporter_user: ExporterUser, case: Case) -> {}:
    if exporter_user:
        return {
            "total": ExporterNotification.objects.filter(
                user=exporter_user, organisation=exporter_user.organisation, case=case
            ).count()
        }

    return {"total": 0}


def get_exporter_user_notifications_individual_counts(exporter_user: ExporterUser, case: Case) -> {}:
    if exporter_user:
        # Group by content_type (casenote, ecjuquery, generatedcasedocument).
        # Get the total number of notifications for each type
        queryset = (
            ExporterNotification.objects.filter(user=exporter_user, organisation=exporter_user.organisation, case=case)
            .values("content_type__model")
            .annotate(count=Count("content_type__model"))
        )

        # Set the model name as the key and the count as the value.
        return {content_type["content_type__model"]: content_type["count"] for content_type in queryset}

    return {}
