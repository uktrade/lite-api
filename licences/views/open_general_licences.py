from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from open_general_licences.helpers import get_open_general_licence
from open_general_licences.models import OpenGeneralLicenceCase
from organisations.libraries.get_organisation import get_request_user_organisation
from organisations.models import Site
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class Create(APIView):
    authentication_classes = (ExporterAuthentication,)

    def post(self, request, *args, **kwargs):
        organisation = get_request_user_organisation(request)
        open_general_licence = get_open_general_licence(request.data.get("open_general_licence"))
        for site in Site.objects.get_uk_sites(organisation):
            if not OpenGeneralLicenceCase.objects.filter(open_general_licence=open_general_licence, site=site).count():
                OpenGeneralLicenceCase.objects.create(open_general_licence=open_general_licence,
                                                      site=site,
                                                      case_type=open_general_licence.case_type,
                                                      organisation=organisation,
                                                      status=get_case_status_by_status(CaseStatusEnum.FINALISED),
                                                      submitted_at=timezone.now(),
                                                      submitted_by=request.user)
        return JsonResponse(data={"open_general_licence": open_general_licence.id}, status=status.HTTP_201_CREATED)
