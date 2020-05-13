from compat import JsonResponse
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from cases.enforcement_check.export_xml import export_cases_xml
from cases.models import Case
from conf.authentication import GovAuthentication
from conf.constants import GovPermissions
from conf.permissions import assert_user_has_permission
from flags.enums import SystemFlags
from flags.models import Flag
from lite_content.lite_api.strings import Cases


class EnforcementCheckView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, queue_pk):
        """
        Fetch enforcement check XML for cases on queue
        """
        assert_user_has_permission(request.user, GovPermissions.ENFORCEMENT_CHECK)
        cases = Case.objects.filter(queues=queue_pk, flags=Flag.objects.get(id=SystemFlags.ENFORCEMENT_CHECK_REQUIRED))

        if not cases:
            return JsonResponse({"errors": [Cases.EnforcementCheck.NO_CASES]}, status=status.HTTP_400_BAD_REQUEST)

        xml = export_cases_xml(cases.values_list("pk", flat=True))

        for case in cases:
            audit_trail_service.create(
                actor=request.user, verb=AuditType.ENFORCEMENT_CHECK, target=case,
            )

        return HttpResponse(xml, content_type="text/xml")
