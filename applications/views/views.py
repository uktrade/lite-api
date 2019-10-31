from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from applications.creators import validate_application_ready_for_submission
from applications.enums import ApplicationType
from applications.helpers import get_application_create_serializer
from applications.libraries.application_helpers import get_serializer_for_application, optional_str_to_bool, \
    validate_status_can_be_set_by_exporter_user, validate_status_can_be_set_by_gov_user
from applications.libraries.case_activity import set_application_ref_number_case_activity, \
    set_application_name_case_activity, set_application_status_case_activity
from applications.libraries.get_applications import get_application
from applications.models import GoodOnApplication, StandardApplication, OpenApplication, BaseApplication, HmrcQuery
from applications.serializers.serializers import BaseApplicationSerializer, ApplicationStatusUpdateSerializer, \
    DraftApplicationCreateSerializer, ApplicationUpdateSerializer
from applications.serializers.hmrc import HmrcQueryUpdateSerializer, HmrcQueryViewSerializer
from cases.models import Case
from conf.authentication import ExporterAuthentication, SharedAuthentication
from conf.constants import Permissions
from conf.decorators import authorised_users, application_in_major_editable_state
from conf.permissions import assert_user_has_permission
from goods.enums import GoodStatus
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
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
        serializer = get_application_create_serializer(data.get('application_type'))
        serializer = serializer(data=data)

        if not serializer.is_valid():
            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)

        application = serializer.save()

        return JsonResponse(data={'id': application.id},  status=status.HTTP_201_CREATED)


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
    def put(self, request, application: BaseApplication):
        """
        Update an application instance.
        """
        if application.application_type == ApplicationType.HMRC_QUERY:
            serializer = HmrcQueryUpdateSerializer(application, data=request.data, partial=True)

            if not serializer.is_valid():
                return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            return JsonResponse(data={}, status=status.HTTP_200_OK)
        else:
            application_old_name = application.name
            application_old_ref_number = application.reference_number_on_information_form
            serializer = ApplicationUpdateSerializer(application, data=request.data, partial=True)

            if not serializer.is_valid():
                return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()

            if request.data.get('name'):
                set_application_name_case_activity(application_old_name, serializer.data.get('name'), request.user,
                                                   application)
            elif request.data.get('reference_number_on_information_form'):
                set_application_ref_number_case_activity(application_old_ref_number,
                                                         serializer.data.get('reference_number_on_information_form'),
                                                         request.user, application)

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
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def put(self, request, application):
        """
        Submit a draft-application which will set its submitted_at datetime and status before creating a case
        """
        previous_application_status = application.status

        errors = validate_application_ready_for_submission(application)
        if errors:
            return JsonResponse(data={'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        application.submitted_at = timezone.now()
        application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        application.save()

        if application.application_type == ApplicationType.STANDARD_LICENCE:
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
            set_application_status_case_activity(application.status.status, request.user, application)

        return JsonResponse(data=data, status=status.HTTP_200_OK)


class ApplicationManageStatus(APIView):
    authentication_classes = (SharedAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        application = get_application(pk)

        data = request.data
        new_status_enum = data.get('status')

        if isinstance(request.user, ExporterUser):
            if request.user.organisation.id != application.organisation.id:
                raise PermissionDenied()

            validation_error = validate_status_can_be_set_by_exporter_user(application.status.status, new_status_enum)
        else:
            validation_error = validate_status_can_be_set_by_gov_user(application.status.status, new_status_enum)

        if validation_error:
            return JsonResponse(data={'errors': [validation_error]}, status=status.HTTP_400_BAD_REQUEST)

        # Only allow the final decision if the user has the MANAGE_FINAL_ADVICE permission
        # This can return 403 forbidden
        if new_status_enum == CaseStatusEnum.FINALISED:
            assert_user_has_permission(request.user, Permissions.MANAGE_FINAL_ADVICE)

        new_status = get_case_status_by_status(new_status_enum)
        request.data['status'] = str(new_status.pk)
        serializer = ApplicationStatusUpdateSerializer(application, data=data, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        set_application_status_case_activity(new_status.status, request.user, application)

        return JsonResponse(data={}, status=status.HTTP_200_OK)
