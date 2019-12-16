from django.contrib.contenttypes.models import ContentType

from users.models import ExporterNotification


def delete_notifications(user, organisation, objects):
    for obj in objects:
        try:
            content_type = ContentType.objects.get_for_model(type(obj))
        except ContentType.DoesNotExist:
            raise Exception("mark_notifications_as_viewed: object type not expected")
        ExporterNotification.objects.filter(user=user, organisation=organisation, content_type=content_type).delete()
