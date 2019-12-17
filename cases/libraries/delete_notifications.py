from organisations.models import Organisation
from users.models import ExporterNotification, ExporterUser


def delete_exporter_notifications(user: ExporterUser, organisation: Organisation, objects: [object]):
    for obj in objects:
        ExporterNotification.objects.filter(user=user, organisation=organisation, object_id=obj.id).delete()
