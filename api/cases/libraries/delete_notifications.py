from api.users.models import ExporterNotification, ExporterUser


def delete_exporter_notifications(user: ExporterUser, organisation_id, objects: list):
    id_list = [obj.id for obj in objects]
    ExporterNotification.objects.filter(
        user=user.baseuser_ptr, organisation_id=organisation_id, object_id__in=id_list
    ).delete()
