import json
from datetime import datetime, timezone

from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.creators import check_application_for_errors
from applications.enums import ApplicationLicenceType
from applications.libraries.application_helpers import get_serializer_for_application
from applications.libraries.get_applications import get_application, get_applications_for_organisation, \
    get_draft_application_for_organisation
from applications.models import GoodOnApplication, StandardApplication, OpenApplication
from applications.serializers import BaseApplicationSerializer, ApplicationUpdateSerializer, \
    DraftApplicationCreateSerializer
from cases.libraries.activity_types import CaseActivityType
from cases.models import Case, CaseActivity
from conf.authentication import ExporterAuthentication, SharedAuthentication
from conf.constants import Permissions
from conf.permissions import assert_user_has_permission
from goods.enums import GoodStatus
from organisations.libraries.get_organisation import get_organisation_by_user
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status_enum


class ApplicationList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        List all applications
        """
        submitted = request.GET.get('submitted', None)

        organisation = get_organisation_by_user(request.user)
        try:
            applications = get_applications_for_organisation(organisation, submitted).order_by('created_at')
        except ValueError as e:
            return JsonResponse(data={'errors': e}, status=status.HTTP_400_BAD_REQUEST)

        # serializer = ApplicationListSerializer(applications, many=True)
        serializer = BaseApplicationSerializer(applications, many=True)

        return JsonResponse(data={'applications': serializer.data})

    def post(self, request):
        organisation = get_organisation_by_user(request.user)
        data = request.data
        data['organisation'] = str(organisation.id)

        # Use generic serializer to validate all types of application as we may not yet know the application type
        serializer = DraftApplicationCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.validated_data['organisation'] = organisation

            # Use the data from the generic serializer to determine which model to save to
            if serializer.validated_data['licence_type'] == ApplicationLicenceType.STANDARD_LICENCE:
                application = StandardApplication(**serializer.validated_data)
            else:
                application = OpenApplication(**serializer.validated_data)

            application.save()

            return JsonResponse(data={'application': {**serializer.data, 'id': str(application.id)}},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class ApplicationDetail(APIView):
    """
    Retrieve or update an application instance.
    """
    authentication_classes = [SharedAuthentication]
    serializer_class = BaseApplicationSerializer

    def get(self, request, pk):
        """
        Retrieve an application instance.
        """
        application = get_application(pk)
        serializer = self.serializer_class(application)
        return JsonResponse(data={'application': serializer.data})

    def put(self, request, pk):
        """
        Update an application instance.
        """
        application = get_application(pk)

        data = json.loads(request.body)

        # Only allow the final decision if the user has the MANAGE_FINAL_ADVICE permission
        if data.get('status') == CaseStatusEnum.FINALISED:
            assert_user_has_permission(request.user, Permissions.MANAGE_FINAL_ADVICE)

        request.data['status'] = str(get_case_status_from_status_enum(data.get('status')).pk)

        serializer = ApplicationUpdateSerializer(get_application(pk), data=request.data, partial=True)

        if serializer.is_valid():
            CaseActivity.create(activity_type=CaseActivityType.UPDATED_STATUS,
                                case=application.case.get(),
                                user=request.user,
                                status=data.get('status'))

            serializer.save()
            return JsonResponse(data={'application': serializer.data})

        return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ApplicationSubmission(APIView):
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        """
        Submit a draft-application which will set its submitted_at datetime and status before creating a case
        """
        draft = get_draft_application_for_organisation(pk, get_organisation_by_user(request.user))

        errors = check_application_for_errors(draft)
        if errors:
            return JsonResponse(data={'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        draft.submitted_at = datetime.now(timezone.utc)
        draft.status = get_case_status_from_status_enum(CaseStatusEnum.SUBMITTED)
        draft.save()

        if draft.licence_type == ApplicationLicenceType.STANDARD_LICENCE:
            for good_on_application in GoodOnApplication.objects.filter(application=draft):
                good_on_application.good.status = GoodStatus.SUBMITTED
                good_on_application.good.save()

        case = Case(application=draft)
        case.save()

        # Serialize for the response message
        serializer = get_serializer_for_application(draft)
        return JsonResponse(data={'application': {**serializer.data, 'case_id': case.id}},
                            status=status.HTTP_200_OK)
