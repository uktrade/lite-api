from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from api.applications.libraries.get_applications import get_application
from api.applications.models import ApplicationException, PartyOnApplication
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.core.authentication import ExporterAuthentication
from api.core.decorators import (
    authorised_to_view_application,
    allowed_party_type_for_open_application_goodstype_category,
    application_in_state,
)
from api.core.helpers import str_to_bool
from lite_content.lite_api import strings
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.parties.enums import PartyType
from api.parties.models import Party
from api.parties.serializers import PartySerializer
from api.users.models import ExporterUser


class ApplicationPartyView(APIView):
    authentication_classes = (ExporterAuthentication,)

    @property
    def application(self):
        return get_application(self.kwargs["pk"])

    @property
    def party(self):
        application = get_application(self.kwargs["pk"])
        party_on_application = application.active_parties.get(party_id=self.kwargs["party_pk"])
        return party_on_application.party

    @allowed_party_type_for_open_application_goodstype_category()
    @authorised_to_view_application(ExporterUser)
    @application_in_state(is_major_editable=True)
    def post(self, request, pk):
        """
        Add a party to an application
        """
        application = get_application(pk)

        data = request.data
        data["organisation"] = get_request_user_organisation_id(request)

        serializer = PartySerializer(data=data, application_type=application.case_type.sub_type)

        if serializer.is_valid(raise_exception=True):
            if str_to_bool(data.get("validate_only", False)):
                return JsonResponse(data={data["type"]: serializer.initial_data}, status=status.HTTP_200_OK)

            # Save party and add to application
            serializer.save()

            try:
                party, removed_party = application.add_party(serializer.instance)
            except ApplicationException as exc:
                return JsonResponse(data={"errors": exc.data}, status=status.HTTP_400_BAD_REQUEST)

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
                payload={"party_type": party.type, "party_name": party.name},
            )

            return JsonResponse(data={party.type: serializer.data}, status=status.HTTP_201_CREATED)

    @authorised_to_view_application(ExporterUser)
    def delete(self, request, pk, party_pk):
        """
        Removes a party from application.
        """
        application = get_application(pk)

        try:
            poa = application.active_parties.all().get(party__pk=party_pk)
        except PartyOnApplication.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

        if not application.party_is_editable(poa.party):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.INVALID_OPERATION_FOR_READ_ONLY_CASE_ERROR]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete party
        application.delete_party(poa)

        # Audit
        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.REMOVE_PARTY,
            target=application.get_case(),
            payload={
                "party_type": poa.party.type.replace("_", " "),
                "party_name": poa.party.name,
            },
        )

        return JsonResponse(data={"party": PartySerializer(poa.party).data}, status=status.HTTP_200_OK)

    @authorised_to_view_application(ExporterUser)
    def get(self, request, **kwargs):
        """
        Get parties for an application
        """
        party_pk = self.kwargs.get("party_pk")
        if party_pk:
            party_data = PartySerializer(self.party).data
            return JsonResponse(data={"type": party_data["type"], "data": party_data})

        application_parties = (
            self.application.active_parties.all().filter(deleted_at__isnull=True).select_related("party")
        )

        if "type" in request.GET:
            application_parties = application_parties.filter(party__type=request.GET["type"])

        parties_data = PartySerializer([p.party for p in application_parties], many=True).data

        key = PartyType.api_key_name(request.GET["type"]) if "type" in request.GET else "parties"

        return JsonResponse(data={key: parties_data})

    @authorised_to_view_application(ExporterUser)
    def put(self, request, **kwargs):
        serializer = PartySerializer(instance=self.party, data=request.data, partial=True)
        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        party_data = serializer.data
        return JsonResponse(data={party_data["type"]: party_data})


class CopyPartyView(APIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_to_view_application(ExporterUser)
    def get(self, request, pk, party_pk):
        """
        Get parties for an application
        """

        detail = Party.objects.copy_detail(pk=party_pk)

        return JsonResponse(data={"party": detail})
