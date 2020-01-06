from organisations.models import Organisation
from users.models import ExporterNotification, ExporterUser, GovNotification, GovUser


def delete_exporter_notifications(user: ExporterUser, organisation: Organisation, objects: list):
    for obj in objects:
        ExporterNotification.objects.filter(user=user, organisation=organisation, object_id=obj.id).delete()


def delete_gov_user_notifications(user: GovUser, objects: list):
    for obj in objects:
        GovNotification.objects.filter(user=user, object_id=obj.id).delete()
