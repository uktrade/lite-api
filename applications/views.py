import json

import reversion
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.creators import create_open_licence, create_standard_licence
from applications.enums import ApplicationLicenceType
from applications.libraries.get_application import get_application_by_pk
from applications.models import Application
from applications.serializers import ApplicationBaseSerializer, ApplicationUpdateSerializer, ApplicationCaseNotesSerializer
from cases.enums import CaseType
from cases.models import Case
from clc_queries.models import ClcQuery
from conf.authentication import ExporterAuthentication, GovAuthentication, SharedAuthentication
from conf.constants import Permissions
from conf.permissions import has_permission
from content_strings.strings import get_string
from drafts.libraries.get_draft import get_draft_with_organisation
from drafts.models import SiteOnDraft, ExternalLocationOnDraft
from goods.enums import GoodStatus
from goods.libraries.get_good import get_good
from organisations.libraries.get_organisation import get_organisation_by_user
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status


class ApplicationList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        List all applications
        """
        organisation = get_organisation_by_user(request.user)

        applications = Application.objects.filter(organisation=organisation).order_by('created_at')
        serializer = ApplicationBaseSerializer(applications, many=True)

        return JsonResponse(data={'applications': serializer.data},
                            )

    @transaction.atomic
    def post(self, request):
        """
        Create a new application from a draft
        """

        submit_id = json.loads(request.body).get('id')

        with reversion.create_revision():
            # Get Draft
            draft = get_draft_with_organisation(submit_id, get_organisation_by_user(request.user))

            # Create an Application object corresponding to the draft
            application = Application(id=draft.id,
                                      name=draft.name,
                                      activity=draft.activity,
                                      licence_type=draft.licence_type,
                                      export_type=draft.export_type,
                                      reference_number_on_information_form=draft.reference_number_on_information_form,
                                      usage=draft.usage,
                                      created_at=draft.created_at,
                                      last_modified_at=draft.last_modified_at,
                                      organisation=draft.organisation,
                                      status=get_case_status_from_status(CaseStatusEnum.SUBMITTED))

            errors = {}

            # Generic errors
            if len(SiteOnDraft.objects.filter(draft=draft)) == 0 \
                    and len(ExternalLocationOnDraft.objects.filter(draft=draft)) == 0:
                errors['location'] = get_string('applications.generic.no_location_set')

            # Create the application depending on type
            if draft.licence_type == ApplicationLicenceType.STANDARD_LICENCE:
                application = create_standard_licence(draft, application, errors)
            elif draft.licence_type == ApplicationLicenceType.OPEN_LICENCE:
                application = create_open_licence(draft, application, errors)

            if not isinstance(application, Application):
                return application

            # Store meta-information.
            reversion.set_user(request.user)
            reversion.set_comment("Created Application Revision")

            # Delete draft
            draft.delete()

            # Create a case
            case = Case(application=application)
            case.save()

            # Add said case to default queue
            queue = Queue.objects.get(pk='00000000-0000-0000-0000-000000000001')
            queue.cases.add(case)
            queue.save()

            serializer = ApplicationBaseSerializer(application)
            return JsonResponse(data={'application': {**serializer.data, 'case_id': case.id}},
                                status=status.HTTP_201_CREATED)


class ApplicationDetail(APIView):
    authentication_classes = [SharedAuthentication]
    serializer_class = ApplicationBaseSerializer

    """
    Retrieve, update or delete a application instance.
    """

    def get(self, request, pk):
        """
        Retrieve an application instance.
        """
        application = get_application_by_pk(pk)
        serializer = self.serializer_class(application)
        return JsonResponse(data={'application': serializer.data})

    def put(self, request, pk):
        """
        Update an application instance.
        """
        with reversion.create_revision():
            data = json.loads(request.body)

            # Only allow the final decision if the user has the MAKE_FINAL_DECISIONS permission
            if data.get('status') == CaseStatusEnum.APPROVED or data.get('status') == CaseStatusEnum.DECLINED:
                has_permission(request.user, Permissions.MAKE_FINAL_DECISIONS)

            request.data['status'] = str(get_case_status_from_status(data.get('status')).pk)

            serializer = ApplicationUpdateSerializer(get_application_by_pk(pk), data=request.data, partial=True)

            if serializer.is_valid():
                # Set audit information
                reversion.set_comment("Updated Application Details")
                reversion.set_user(self.request.user)

                serializer.save()
                return JsonResponse(data={'application': serializer.data})

            return JsonResponse(data={'errors': serializer.errors}, status=400)


class CLCList(APIView):
    def post(self, request):
        data = JSONParser().parse(request)
        good = get_good(data['good_id'])

        good.status = GoodStatus.SUBMITTED
        if data['not_sure_details_control_code'] == '':
            return JsonResponse(data={'errors': {
                'not_sure_details_control_code': [ErrorDetail('This field may not be blank.', code='blank')]
            }}, status=status.HTTP_400_BAD_REQUEST)
        good.control_code = data['not_sure_details_control_code']
        good.save()

        clc_query = ClcQuery(details=data['not_sure_details_details'],
                             good=good,
                             status=get_case_status_from_status(CaseStatusEnum.SUBMITTED))
        clc_query.save()

        # Create a case
        case = Case(clc_query=clc_query, type=CaseType.CLC_QUERY)
        case.save()

        # Add said case to default queue
        queue = Queue.objects.get(pk='00000000-0000-0000-0000-000000000001')
        queue.cases.add(case)
        queue.save()

        return JsonResponse(data={'id': clc_query.id, 'case_id': case.id }, status=status.HTTP_201_CREATED)
