from django.db.models import Count

from users.models import ExporterNotification, ExporterUser
from cases.models import Case


def get_exporter_user_notifications_total_count(exporter_user: ExporterUser, case: Case) -> {}:
    notifications_total_count = {"total": 0}

    if exporter_user:
        notifications_total_count["total"] = ExporterNotification.objects.filter(
            user=exporter_user, organisation=exporter_user.organisation, case=case
        ).count()

    return notifications_total_count


def get_exporter_user_notifications_individual_counts(exporter_user: ExporterUser, case: Case) -> {}:
    notifications_individual_counts = {"total": 0}

    if exporter_user:
        queryset = (
            ExporterNotification.objects.filter(user=exporter_user, organisation=exporter_user.organisation, case=case)
            .values("content_type__model")
            .annotate(count=Count("content_type__model"))
        )

        for content_type in queryset:
            notifications_individual_counts[content_type["content_type__model"]] = content_type["count"]
            notifications_individual_counts["total"] += content_type["count"]

    return notifications_individual_counts
