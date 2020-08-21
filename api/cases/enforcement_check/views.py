from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.enforcement_check.export_xml import export_cases_xml
from api.cases.enforcement_check.import_xml import import_cases_xml
from api.cases.models import Case
from api.core.authentication import GovAuthentication
from api.core.constants import GovPermissions
from api.core.permissions import assert_user_has_permission
from api.flags.enums import SystemFlags
from api.flags.models import Flag
from lite_content.lite_api.strings import Cases
from api.queues.models import Queue


class EnforcementCheckView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, queue_pk):
        """
        Fetch enforcement check XML for cases on queue
        """
        assert_user_has_permission(request.user, GovPermissions.ENFORCEMENT_CHECK)
        cases = Case.objects.filter(queues=queue_pk, flags=Flag.objects.get(id=SystemFlags.ENFORCEMENT_CHECK_REQUIRED))

        if not cases:
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)

        xml = export_cases_xml(cases)

        for case in cases:
            audit_trail_service.create(
                actor=request.user, verb=AuditType.ENFORCEMENT_CHECK, target=case,
            )

        return HttpResponse(xml, content_type="text/xml")

    def post(self, request, queue_pk):
        assert_user_has_permission(request.user, GovPermissions.ENFORCEMENT_CHECK)
        file = request.data.get("file")
        if not file:
            raise ValidationError({"file": [Cases.EnforcementUnit.NO_FILE_ERROR]})

        queue = get_object_or_404(Queue, id=queue_pk)
        import_cases_xml(file, queue)
        return JsonResponse({"file": Cases.EnforcementUnit.SUCCESSFUL_UPLOAD})
