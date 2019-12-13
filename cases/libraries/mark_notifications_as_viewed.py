from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from cases.models import BaseNotification


def mark_notifications_as_viewed(user, objects):
    for obj in objects:
        try:
            content_type = ContentType.objects.get_for_model(type(obj))
        except ContentType.DoesNotExist:
            raise Exception("mark_notifications_as_viewed: object type not expected")

        BaseNotification.objects.filter(user=user, content_type=content_type).update(viewed_at=timezone.now())
