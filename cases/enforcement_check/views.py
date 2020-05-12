from django.http import HttpResponse
from rest_framework.views import APIView

from cases.enforcement_check.export_xml import export_cases_xml
from cases.enums import CaseTypeTypeEnum
from cases.models import Case, CaseType
from conf.authentication import GovAuthentication


class EnforcementCheckView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, queue_pk):
        """
        Fetch enforcement check XML for cases on queue
        """
        query_types = CaseType.objects.filter(type=CaseTypeTypeEnum.QUERY)
        application_ids = (
            Case.objects.filter(queues=queue_pk).exclude(case_type__in=query_types).values_list("pk", flat=True)
        )

        xml = export_cases_xml(application_ids)
        return HttpResponse(xml, content_type='text/xml')
