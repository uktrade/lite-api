from datetime import datetime, timezone

from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from applications.creators import validate_application_ready_for_submission
from applications.enums import ApplicationLicenceType
from applications.libraries.application_helpers import get_serializer_for_application, optional_str_to_bool, \
    validate_status_can_be_set
from applications.libraries.get_applications import get_application
from applications.models import GoodOnApplication, StandardApplication, OpenApplication, BaseApplication
from applications.serializers import BaseApplicationSerializer, ApplicationStatusUpdateSerializer, \
    DraftApplicationCreateSerializer, ApplicationUpdateSerializer
from cases.libraries.activity_types import CaseActivityType
from cases.models import Case, CaseActivity
from conf.authentication import ExporterAuthentication, SharedAuthentication
from conf.constants import Permissions
from conf.decorators import authorised_users
from conf.permissions import assert_user_has_permission
from goods.enums import GoodStatus
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status_enum
from users.models import ExporterUser


class ApplicationList(ListAPIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, *args, **kwargs):
        """
        List all applications
        """
        try:
            submitted = optional_str_to_bool(request.GET.get('submitted'))
        except ValueError as e:
            return JsonResponse(data={'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if submitted is None:
            qs = BaseApplication.objects.filter(organisation=request.user.organisation)
        elif submitted:
            qs = BaseApplication.objects.submitted(organisation=request.user.organisation)
        else:
            qs = BaseApplication.objects.draft(organisation=request.user.organisation)

        applications = qs.order_by('created_at')

        serializer = BaseApplicationSerializer(applications, many=True)

        return JsonResponse(data={'applications': serializer.data})

    def post(self, request):
        data = request.data
        data['organisation'] = str(request.user.organisation.id)

        # Use generic serializer to validate all types of application as we may not yet know the application type
        serializer = DraftApplicationCreateSerializer(data=data)

        if not serializer.is_valid():
            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)

        serializer.validated_data['organisation'] = request.user.organisation

        # Use the data from the generic serializer to determine which model to save to
        if serializer.validated_data['licence_type'] == ApplicationLicenceType.STANDARD_LICENCE:
            application = StandardApplication(**serializer.validated_data)
        else:
            application = OpenApplication(**serializer.validated_data)

        application.save()

        return JsonResponse(data={'application': {**serializer.data, 'id': str(application.id)}},
                            status=status.HTTP_201_CREATED)


class ApplicationDetail(APIView):
    """
    Retrieve or update an application instance.
    """
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        Retrieve an application instance.
        """
        serializer = get_serializer_for_application(application)
        return JsonResponse(data={'application': serializer.data})

    @authorised_users(ExporterUser)
    def put(self, request, application):
        """
        Update an application instance.
        """
        serializer = ApplicationUpdateSerializer(application, data=request.data, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        if application.case.get():
            kwargs = {
                'case': application.case.get(),
                'user': request.user
            }

            if request.data.get('name'):
                kwargs['application_name'] = request.data.get('name')
                CaseActivity.create(activity_type=CaseActivityType.UPDATED_APPLICATION_NAME, **kwargs)
            elif request.data.get('reference_number_on_information_form'):
                kwargs['application_reference_number'] = request.data.get('reference_number_on_information_form')
                CaseActivity.create(activity_type=CaseActivityType.UPDATED_APPLICATION_REFERENCE_NUMBER, **kwargs)

        return JsonResponse(data={}, status=status.HTTP_200_OK)

    @authorised_users(ExporterUser)
    def delete(self, request, application):
        """
        Deleting an application should only be allowed for draft applications
        """
        if application.submitted_at:
            return JsonResponse(data={'errors': 'Only draft applications can be deleted'},
                                status=status.HTTP_400_BAD_REQUEST)
        application.delete()
        return JsonResponse(data={'status': 'Draft application deleted'},
                            status=status.HTTP_200_OK)


class ApplicationSubmission(APIView):
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    @authorised_users(ExporterUser)
    def put(self, request, application):
        """
        Submit a draft-application which will set its submitted_at datetime and status before creating a case
        """
        previous_application_status = application.status

        errors = validate_application_ready_for_submission(application)
        if errors:
            return JsonResponse(data={'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        application.submitted_at = datetime.now(timezone.utc)
        application.status = get_case_status_from_status_enum(CaseStatusEnum.SUBMITTED)
        application.save()

        if application.licence_type == ApplicationLicenceType.STANDARD_LICENCE:
            for good_on_application in GoodOnApplication.objects.filter(application=application):
                if good_on_application.good.status == GoodStatus.DRAFT:
                    good_on_application.good.status = GoodStatus.SUBMITTED
                    good_on_application.good.save()

        # Serialize for the response message
        serializer = get_serializer_for_application(application)

        data = {'application': {**serializer.data}}

        if not previous_application_status:
            # If the application is being submitted for the first time
            case = Case(application=application)
            case.save()
            data['application']['case_id'] = case.id
        else:
            # If the application is being submitted after being edited
            CaseActivity.create(activity_type=CaseActivityType.UPDATED_STATUS,
                                case=application.case.get(),
                                user=request.user,
                                status=application.status.status)

        return JsonResponse(data=data, status=status.HTTP_200_OK)


class ApplicationManageStatus(APIView):
    authentication_classes = (SharedAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        application = get_application(pk)

        data = request.data
        new_status_enum = data.get('status')

        # Only allow the final decision if the user has the MANAGE_FINAL_ADVICE permission
        # This can return 403 forbidden
        if new_status_enum == CaseStatusEnum.FINALISED:
            assert_user_has_permission(request.user, Permissions.MANAGE_FINAL_ADVICE)

        if isinstance(request.user, ExporterUser) and request.user.organisation.id != application.organisation.id:
            raise PermissionDenied()

        validation_error = validate_status_can_be_set(application.status.status, new_status_enum, request.user)

        if validation_error:
            return JsonResponse(data={'errors': [validation_error]}, status=status.HTTP_400_BAD_REQUEST)

        new_status = get_case_status_from_status_enum(new_status_enum)

        request.data['status'] = str(new_status.pk)
        serializer = ApplicationStatusUpdateSerializer(application, data=data, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        CaseActivity.create(activity_type=CaseActivityType.UPDATED_STATUS,
                            case=application.case.get(),
                            user=request.user,
                            status=new_status.status)

        return JsonResponse(data={}, status=status.HTTP_200_OK)
