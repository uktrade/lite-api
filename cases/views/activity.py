from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import JsonResponse
from rest_framework.views import APIView

from audit_trail.models import Audit
from audit_trail.serializers import AuditSerializer
from cases.libraries.get_case import get_case
from conf.authentication import GovAuthentication


class Activity(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Retrieves all activity related to a case
    * Case Updates
    * Case Notes
    * ECJU Queries
    """
    def get(self, request, pk):
        case = get_case(pk)

        qudit_qs = Audit.objects.all()

        case_as_action_filter = Q(
            action_object_object_id=case.id,
            action_object_content_type=ContentType.objects.get_for_model(case)
        )
        case_as_target_filter = Q(
            target_object_id=case.id,
            target_content_type=ContentType.objects.get_for_model(case)
        )

        actions = qudit_qs.filter(case_as_action_filter | case_as_target_filter)

        serializer = AuditSerializer(actions, many=True)

        return JsonResponse(data={"activity": serializer.data})
