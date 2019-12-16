from users.models import ExporterNotification


def delete_exporter_notifications(user, organisation, objects):
    for obj in objects:
        ExporterNotification.objects.filter(user=user, organisation=organisation, object_id=obj.id).delete()
