from api.users.models import ExporterNotification, ExporterUser, GovNotification, GovUser


def delete_exporter_notifications(user: ExporterUser, organisation_id, objects: list):
    id_list = [obj.id for obj in objects]
    ExporterNotification.objects.filter(user=user, organisation_id=organisation_id, object_id__in=id_list).delete()


def delete_gov_user_notifications(user: GovUser, id_list: list):
    GovNotification.objects.filter(user=user, object_id__in=id_list).delete()
