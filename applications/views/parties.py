from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationType
from applications.models import ApplicationException, PartyOnApplication
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from conf.authentication import ExporterAuthentication
from conf.decorators import (
    authorised_users,
    allowed_application_types,
)
from conf.helpers import str_to_bool
from parties.enums import PartyType
from parties.serializers import PartySerializer
from users.models import ExporterUser


class ApplicationPartyView(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Add a party to an application.
        """
        data = request.data
        data["organisation"] = request.user.organisation.id

        # Validate data
        serializer = PartySerializer(data=data)
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
                target=application,
                payload={"party_type": removed_party.type.replace("_", " "), "party_name": removed_party.name},
            )

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.ADD_PARTY,
            target=application,
            payload={"party_type": party.type.replace("_", " "), "party_name": party.name},
        )

        return JsonResponse(data={party.type: serializer.data}, status=status.HTTP_201_CREATED)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
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
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
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

        key = PartyType.api_compatible(request.GET["type"]) if "type" in request.GET else "parties"

        return JsonResponse(data={key: parties_data})
