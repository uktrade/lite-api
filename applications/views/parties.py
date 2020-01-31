from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationType
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from conf.authentication import ExporterAuthentication
from conf.decorators import (
    authorised_users,
    application_in_major_editable_state,
    application_in_editable_state,
    allowed_application_types,
)
from conf.helpers import str_to_bool
from parties.helpers import delete_party_document_if_exists
from parties.models import UltimateEndUser, ThirdParty
from parties.serializers import (
    EndUserSerializer,
    UltimateEndUserSerializer,
    ConsigneeSerializer,
    ThirdPartySerializer,
)
from users.models import ExporterUser


class ApplicationEndUser(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Create an end user and add it to a application
        """
        data = request.data
        data["organisation"] = request.user.organisation.id
        case = application.get_case()

        serializer = EndUserSerializer(data=data)
        if str_to_bool(data.get("validate_only")):
            if serializer.is_valid():
                return JsonResponse(data={"end_user": serializer.initial_data}, status=status.HTTP_200_OK)
        else:
            if serializer.is_valid():
                previous_end_user = application.end_user

                new_end_user = serializer.save()
                application.end_user = new_end_user
                application.save()
                if previous_end_user:
                    delete_party_document_if_exists(previous_end_user)
                    previous_end_user.delete()
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.REMOVE_PARTY,
                        target=case,
                        payload={
                            "party_type": previous_end_user.type.replace("_", " "),
                            "party_name": previous_end_user.name,
                        },
                    )

                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ADD_PARTY,
                    target=case,
                    payload={"party_type": new_end_user.type.replace("_", " "), "party_name": new_end_user.name,},
                )

                return JsonResponse(data={"end_user": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def delete(self, request, application):
        """
        Delete an end user and their document from an application
        """
        end_user = application.end_user

        if not end_user:
            return JsonResponse(data={"errors": "end user not found"}, status=status.HTTP_404_NOT_FOUND)

        application.end_user = None
        application.save()
        delete_party_document_if_exists(end_user)
        end_user.delete()

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.REMOVE_PARTY,
            target=application.get_case(),
            payload={"party_type": end_user.type.replace("_", " "), "party_name": end_user.name,},
        )

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class ApplicationUltimateEndUsers(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        Get ultimate end users associated with a application
        """
        ueu_data = UltimateEndUserSerializer(application.ultimate_end_users, many=True).data

        return JsonResponse(data={"ultimate_end_users": ueu_data})

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Create an ultimate end user and add it to a application
        """
        data = request.data
        data["organisation"] = request.user.organisation.id
        serializer = UltimateEndUserSerializer(data=data)

        if str_to_bool(data.get("validate_only")):
            if serializer.is_valid():
                return JsonResponse(data={"ultimate_end_user": serializer.initial_data}, status=status.HTTP_200_OK)
        else:
            if serializer.is_valid():
                ultimate_end_user = serializer.save()
                application.ultimate_end_users.add(ultimate_end_user.id)

                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ADD_PARTY,
                    target=application.get_case(),
                    payload={
                        "party_type": ultimate_end_user.type.replace("_", " "),
                        "party_name": ultimate_end_user.name,
                    },
                )

                return JsonResponse(data={"ultimate_end_user": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class RemoveApplicationUltimateEndUser(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    @application_in_editable_state()
    def delete(self, request, application, ueu_pk):
        """
        Delete an ultimate end user and remove it from the application
        """
        try:
            ultimate_end_user = application.ultimate_end_users.get(id=ueu_pk)
        except UltimateEndUser.DoesNotExist:
            return JsonResponse(data={"errors": "ultimate end user not found"}, status=status.HTTP_404_NOT_FOUND,)

        application.ultimate_end_users.remove(ultimate_end_user.id)
        delete_party_document_if_exists(ultimate_end_user)
        ultimate_end_user.delete()
        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.REMOVE_PARTY,
            target=application.get_case(),
            payload={"party_type": ultimate_end_user.type.replace("_", " "), "party_name": ultimate_end_user.name,},
        )

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class ApplicationConsignee(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Create a consignee and add it to a application
        """
        data = request.data
        data["organisation"] = request.user.organisation.id
        case = application.get_case()

        serializer = ConsigneeSerializer(data=data)

        if str_to_bool(data.get("validate_only")):
            if serializer.is_valid():
                return JsonResponse(data={"consignee": serializer.initial_data}, status=status.HTTP_200_OK)

        else:
            if serializer.is_valid():
                previous_consignee = application.consignee

                new_consignee = serializer.save()
                application.consignee = new_consignee
                application.save()

                if previous_consignee:
                    delete_party_document_if_exists(previous_consignee)
                    previous_consignee.delete()

                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.REMOVE_PARTY,
                        target=case,
                        payload={
                            "party_type": previous_consignee.type.replace("_", " "),
                            "party_name": previous_consignee.name,
                        },
                    )

                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ADD_PARTY,
                    target=case,
                    payload={"party_type": new_consignee.type.replace("_", " "), "party_name": new_consignee.name,},
                )

                return JsonResponse(data={"consignee": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def delete(self, request, application):
        """
        Delete a consignee and their document from an application
        """
        consignee = application.consignee

        if not consignee:
            return JsonResponse(data={"errors": "consignee not found"}, status=status.HTTP_404_NOT_FOUND)

        application.consignee = None
        application.save()
        delete_party_document_if_exists(consignee)
        consignee.delete()

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.REMOVE_PARTY,
            target=application.get_case(),
            payload={"party_type": consignee.type.replace("_", " "), "party_name": consignee.name,},
        )

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class ApplicationThirdParties(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        Get third parties associated with a application
        """
        third_party_data = ThirdPartySerializer(application.third_parties, many=True).data

        return JsonResponse(data={"third_parties": third_party_data})

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Create a third party and add it to a application
        """
        data = request.data
        data["organisation"] = request.user.organisation.id
        serializer = ThirdPartySerializer(data=data)

        if str_to_bool(data.get("validate_only")):
            if serializer.is_valid():
                return JsonResponse(data={"third_party": serializer.initial_data}, status=status.HTTP_200_OK)
        else:
            if serializer.is_valid():
                third_party = serializer.save()
                application.third_parties.add(third_party.id)

                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ADD_PARTY,
                    target=application.get_case(),
                    payload={"party_type": third_party.type.replace("_", " "), "party_name": third_party.name},
                )

                return JsonResponse(data={"third_party": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class RemoveThirdParty(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(
        [ApplicationType.STANDARD_LICENCE, ApplicationType.HMRC_QUERY, ApplicationType.EXHIBITION_CLEARANCE]
    )
    @authorised_users(ExporterUser)
    @application_in_editable_state()
    def delete(self, request, application, tp_pk):
        """ Delete a third party and remove it from the application. """
        try:
            third_party = application.third_parties.get(pk=tp_pk)
        except ThirdParty.DoesNotExist:
            return JsonResponse(data={"errors": "third party not found"}, status=status.HTTP_404_NOT_FOUND,)

        application.third_parties.remove(third_party.id)
        delete_party_document_if_exists(third_party)
        third_party.delete()

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.REMOVE_PARTY,
            target=application.get_case(),
            payload={"party_type": third_party.type.replace("_", " "), "party_name": third_party.name,},
        )

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
