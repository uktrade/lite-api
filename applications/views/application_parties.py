from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from conf.authentication import ExporterAuthentication
from conf.decorators import application_licence_type, authorised_users, application_in_major_editable_state
from parties.helpers import delete_party_document_if_exists
from parties.models import UltimateEndUser, ThirdParty
from parties.serializers import EndUserSerializer, UltimateEndUserSerializer, ConsigneeSerializer, ThirdPartySerializer
from users.models import ExporterUser


class ApplicationEndUser(APIView):
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Create an end user and add it to a application
        """
        data = request.data
        data['organisation'] = request.user.organisation.id

        serializer = EndUserSerializer(data=data)
        if serializer.is_valid():
            previous_end_user = application.end_user

            new_end_user = serializer.save()
            application.end_user = new_end_user
            application.save()

            if previous_end_user:
                delete_party_document_if_exists(previous_end_user)
                previous_end_user.delete()

            return JsonResponse(data={'end_user': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def delete(self, request, application):
        """
        Delete an end user and their document from an application
        """
        end_user = application.end_user

        if not end_user:
            return JsonResponse(data={'errors': 'consignee not found'}, status=status.HTTP_404_NOT_FOUND)

        if end_user.organisation != request.user.organisation:
            return JsonResponse(data={'errors': 'request invalid'}, status=status.HTTP_400_BAD_REQUEST)

        application.end_user = None
        application.save()
        delete_party_document_if_exists(end_user)
        end_user.delete()

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class ApplicationUltimateEndUsers(APIView):
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        Get ultimate end users associated with a application
        """
        ueu_data = UltimateEndUserSerializer(application.ultimate_end_users, many=True).data

        return JsonResponse(data={'ultimate_end_users': ueu_data})

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Create an ultimate end user and add it to a application
        """
        data = request.data
        data['organisation'] = request.user.organisation.id

        serializer = UltimateEndUserSerializer(data=data)
        if serializer.is_valid():
            ultimate_end_user = serializer.save()
            application.ultimate_end_users.add(ultimate_end_user.id)

            return JsonResponse(data={'ultimate_end_user': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class RemoveApplicationUltimateEndUser(APIView):
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def delete(self, request, application, ueu_pk):
        """
        Delete an ultimate end user and remove it from the application
        """
        try:
            ultimate_end_user = application.ultimate_end_users.get(id=ueu_pk)
        except UltimateEndUser.DoesNotExist:
            return JsonResponse(data={'errors': 'ultimate end user not found'}, status=status.HTTP_404_NOT_FOUND)

        application.ultimate_end_users.remove(ultimate_end_user.id)
        delete_party_document_if_exists(ultimate_end_user)
        ultimate_end_user.delete()

        return JsonResponse(data={'ultimate_end_user': 'deleted'}, status=status.HTTP_200_OK)


class ApplicationConsignee(APIView):
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Create a consignee and add it to a application
        """
        data = request.data
        data['organisation'] = request.user.organisation.id

        serializer = ConsigneeSerializer(data=data)
        if serializer.is_valid():
            previous_consignee = application.consignee

            new_consignee = serializer.save()
            application.consignee = new_consignee
            application.save()

            if previous_consignee:
                delete_party_document_if_exists(previous_consignee)
                previous_consignee.delete()

            return JsonResponse(data={'consignee': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def delete(self, request, application):
        """
        Delete a consignee and their document from an application
        """
        consignee = application.consignee

        if not consignee:
            return JsonResponse(data={'errors': 'consignee not found'}, status=status.HTTP_404_NOT_FOUND)

        application.consignee = None
        application.save()
        delete_party_document_if_exists(consignee)
        consignee.delete()

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class ApplicationThirdParties(APIView):
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        Get third parties associated with a application
        """
        third_party_data = ThirdPartySerializer(application.third_parties, many=True).data

        return JsonResponse(data={'third_parties': third_party_data})

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Create a third party and add it to a application
        """
        data = request.data
        data['organisation'] = request.user.organisation.id

        serializer = ThirdPartySerializer(data=data)
        if serializer.is_valid():
            third_party = serializer.save()
            application.third_parties.add(third_party.id)

            return JsonResponse(data={'third_party': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class RemoveThirdParty(APIView):
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_users(ExporterUser)
    def delete(self, request, application, tp_pk):
        """
        Delete a third party and remove it from the application
        """
        try:
            third_party = application.third_parties.get(pk=tp_pk)
        except ThirdParty.DoesNotExist:
            return JsonResponse(data={'errors': 'third party not found'}, status=status.HTTP_404_NOT_FOUND)

        application.third_parties.remove(third_party.id)
        delete_party_document_if_exists(third_party)
        third_party.delete()

        return JsonResponse(data={'third_party': 'deleted'}, status=status.HTTP_200_OK)
