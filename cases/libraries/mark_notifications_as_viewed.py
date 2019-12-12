from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import CaseNote, Notification, EcjuQuery
from queries.control_list_classifications.models import ControlListClassificationQuery


def mark_notifications_as_viewed(user, objects):
    for obj in objects:
        if isinstance(obj, CaseNote):
            content_type = ContentType.objects.get_for_model(CaseNote)
            Notification.objects.filter(user=user, content_type=content_type).update(viewed_at=timezone.now())
        elif isinstance(obj, EcjuQuery):
            content_type = ContentType.objects.get_for_model(EcjuQuery)
            Notification.objects.filter(user=user, content_type=content_type).update(viewed_at=timezone.now())
        elif isinstance(obj, GeneratedCaseDocument):
            content_type = ContentType.objects.get_for_model(GeneratedCaseDocument)
            Notification.objects.filter(user=user, content_type=content_type).update(viewed_at=timezone.now())
        elif isinstance(obj, ControlListClassificationQuery):
            content_type = ContentType.objects.get_for_model(ControlListClassificationQuery)
            Notification.objects.filter(user=user, content_type=content_type).update(viewed_at=timezone.now())
        else:
            raise Exception("mark_notifications_as_viewed: object type not expected")
