from compat import JsonResponse
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from cases.enforcement_check.export_xml import export_cases_xml
from cases.enums import CaseTypeTypeEnum
from cases.models import Case, CaseType
from conf.authentication import GovAuthentication
from conf.constants import GovPermissions
from conf.permissions import assert_user_has_permission


class EnforcementCheckView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, queue_pk):
        """
        Fetch enforcement check XML for cases on queue
        """
        assert_user_has_permission(request.user, GovPermissions.ENFORCEMENT_CHECK)

        query_types = CaseType.objects.filter(type=CaseTypeTypeEnum.QUERY)
        application_ids = (
            Case.objects.filter(queues=queue_pk).exclude(case_type__in=query_types).values_list("pk", flat=True)
        )

        if not application_ids:
            return JsonResponse({"errors": ["No matching cases found"]}, status=status.HTTP_400_BAD_REQUEST)

        xml = export_cases_xml(application_ids)
        return HttpResponse(xml, content_type="text/xml")
