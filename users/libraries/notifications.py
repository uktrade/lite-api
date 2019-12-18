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
    notifications_individual_counts = {"total": 0}

    if exporter_user:
        # Group by content_type (casenote, ecjuquery, generatedcasedocument).
        # Get the total number of notifications for each type
        queryset = (
            ExporterNotification.objects.filter(user=exporter_user, organisation=exporter_user.organisation, case=case)
            .values("content_type__model")
            .annotate(count=Count("content_type__model"))
        )

        # Iterate through the different types and append to notifications_individual_counts dictionary.
        # Set the model name as the key and the count as the value.
        # Whilst iterating, calculate the total number of notifications instead of executing another query.
        for content_type in queryset:
            notifications_individual_counts[content_type["content_type__model"]] = content_type["count"]
            notifications_individual_counts["total"] += content_type["count"]

    return notifications_individual_counts
