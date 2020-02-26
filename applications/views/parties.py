from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.models import ApplicationException, PartyOnApplication
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.enums import CaseTypeSubTypeEnum
from conf.authentication import ExporterAuthentication
from conf.decorators import (
    authorised_users,
    allowed_application_types,
)
from conf.helpers import str_to_bool
from lite_content.lite_api import strings
from parties.enums import PartyType
from parties.models import Party
from parties.serializers import PartySerializer
from static.statuses.enums import CaseStatusEnum
from users.models import ExporterUser


class ApplicationPartyView(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [
            CaseTypeSubTypeEnum.STANDARD,
            CaseTypeSubTypeEnum.HMRC,
            CaseTypeSubTypeEnum.EXHIBITION,
            CaseTypeSubTypeEnum.GIFTING,
            CaseTypeSubTypeEnum.F680,
        ]
    )
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Add a party to an application.
        """
        data = request.data
        data["organisation"] = request.user.organisation.id

        if not application.is_major_editable():
            return JsonResponse(
                data={
                    "errors": [
                        f"You can only perform this operation when the application is "
                        f"in a `draft` or `{CaseStatusEnum.APPLICANT_EDITING}` state"
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PartySerializer(data=data, application_type=application.case_type.sub_type)

        # Validate data
        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if str_to_bool(data.get("validate_only", False)):
            return JsonResponse(data={data["type"]: serializer.initial_data}, status=status.HTTP_200_OK)

        # Save party and add to application
        serializer.save()
        try:
            party, removed_party = application.add_party(serializer.instance)
        except ApplicationException as exc:
            return JsonResponse(data=exc.data, status=status.HTTP_400_BAD_REQUEST)

        # Audit
        if removed_party:
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.REMOVE_PARTY,
                target=application.get_case(),
                payload={"party_type": removed_party.type.replace("_", " "), "party_name": removed_party.name},
            )
        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.ADD_PARTY,
            target=application.get_case(),
            payload={"party_type": party.type.replace("_", " "), "party_name": party.name},
        )

        return JsonResponse(data={party.type: serializer.data}, status=status.HTTP_201_CREATED)

    @allowed_application_types(
        [
            CaseTypeSubTypeEnum.STANDARD,
            CaseTypeSubTypeEnum.HMRC,
            CaseTypeSubTypeEnum.EXHIBITION,
            CaseTypeSubTypeEnum.GIFTING,
            CaseTypeSubTypeEnum.F680,
        ]
    )
    @authorised_users(ExporterUser)
    def delete(self, request, application, party_pk):
        """
        Removes a party from application.
        """
        try:
            poa = application.active_parties.all().get(party__pk=party_pk)
        except PartyOnApplication.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

        if not application.party_is_editable(poa.party):
            return JsonResponse(
                data={"errors": [strings.Applications.READ_ONLY_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete party
        application.delete_party(poa)

        # Audit
        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.REMOVE_PARTY,
            target=application.get_case(),
            payload={"party_type": poa.party.type.replace("_", " "), "party_name": poa.party.name,},
        )

        return JsonResponse(data={"party": PartySerializer(poa.party).data}, status=status.HTTP_200_OK)

    @allowed_application_types(
        [
            CaseTypeSubTypeEnum.STANDARD,
            CaseTypeSubTypeEnum.HMRC,
            CaseTypeSubTypeEnum.EXHIBITION,
            CaseTypeSubTypeEnum.GIFTING,
            CaseTypeSubTypeEnum.F680,
        ]
    )
    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        Get parties for an application
        """
        application_parties = application.active_parties.all().filter(deleted_at__isnull=True).select_related("party")

        if "type" in request.GET:
            application_parties = application_parties.filter(party__type=request.GET["type"])

        parties_data = PartySerializer([p.party for p in application_parties], many=True).data

        key = PartyType.api_key_name(request.GET["type"]) if "type" in request.GET else "parties"

        return JsonResponse(data={key: parties_data})


class CopyPartyView(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [
            CaseTypeSubTypeEnum.STANDARD,
            CaseTypeSubTypeEnum.HMRC,
            CaseTypeSubTypeEnum.EXHIBITION,
            CaseTypeSubTypeEnum.GIFTING,
            CaseTypeSubTypeEnum.F680,
        ]
    )
    @authorised_users(ExporterUser)
    def get(self, request, application, party_pk):
        """
        Get parties for an application
        """
        detail = Party.objects.copy_detail(pk=party_pk)

        return JsonResponse(data={"party": detail})
