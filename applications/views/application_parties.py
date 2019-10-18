from django.db import transaction
from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from conf.authentication import ExporterAuthentication
from conf.decorators import only_application_type, authorised_user_type
from parties.helpers import delete_party_document_if_exists
from parties.models import UltimateEndUser, ThirdParty, EndUser
from parties.serializers import EndUserSerializer, UltimateEndUserSerializer, ConsigneeSerializer, ThirdPartySerializer
from users.models import ExporterUser


class ApplicationEndUser(APIView):
    authentication_classes = (ExporterAuthentication,)

    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_user_type(ExporterUser)
    def post(self, request, application):
        """
        Create an end user and add it to a application
        """
        data = request.data
        data['organisation'] = str(request.user.organisation.id)

        serializer = EndUserSerializer(data=data)
        if serializer.is_valid():
            previous_end_user = application.end_user

            new_end_user = serializer.save()
            application.end_user = new_end_user
            application.save()

            if previous_end_user:
                delete_party_document_if_exists(previous_end_user)
                previous_end_user.delete()

            return JsonResponse(data={'end_user': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic()
    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_user_type(ExporterUser)
    def delete(self, request, application):
        """
        Delete an end user and their document from an application
        """
        try:
            end_user = EndUser.objects.get(id=application.end_user.id)
        except UltimateEndUser.DoesNotExist:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        if end_user.organisation != request.user.organisation:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        delete_party_document_if_exists(end_user)

        application.end_user = None
        application.save()
        end_user.delete()

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class ApplicationUltimateEndUsers(APIView):
    authentication_classes = (ExporterAuthentication,)

    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_user_type(ExporterUser)
    def get(self, request, application):
        """
        Get ultimate end users associated with a application
        """
        ueu_data = UltimateEndUserSerializer(application.ultimate_end_users, many=True).data

        return JsonResponse(data={'ultimate_end_users': ueu_data})

    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_user_type(ExporterUser)
    def post(self, request, application):
        """
        Create an ultimate end user and add it to a application
        """
        data = request.data
        data['organisation'] = str(request.user.organisation.id)

        serializer = UltimateEndUserSerializer(data=data)
        if serializer.is_valid():
            ultimate_end_user = serializer.save()
            application.ultimate_end_users.add(str(ultimate_end_user.id))
            application.save()

            return JsonResponse(data={'ultimate_end_user': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class ApplicationConsignee(APIView):
    authentication_classes = (ExporterAuthentication,)

    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_user_type(ExporterUser)
    def post(self, request, application):
        """
        Create a consignee and add it to a application
        """
        data = request.data
        data['organisation'] = str(request.user.organisation.id)

        serializer = ConsigneeSerializer(data=data)
        if serializer.is_valid():
            previous_consignee = application.consignee

            new_consignee = serializer.save()
            application.consignee = new_consignee
            application.save()

            if previous_consignee:
                delete_party_document_if_exists(previous_consignee)
                previous_consignee.delete()

            return JsonResponse(data={'consignee': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class ApplicationThirdParties(APIView):
    authentication_classes = (ExporterAuthentication,)

    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_user_type(ExporterUser)
    def get(self, request, application):
        """
        Get third parties associated with a application
        """
        third_party_data = ThirdPartySerializer(application.third_parties, many=True).data

        return JsonResponse(data={'third_parties': third_party_data})

    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_user_type(ExporterUser)
    def post(self, request, application):
        """
        Create a third party and add it to a application
        """
        data = request.data
        data['organisation'] = str(request.user.organisation.id)

        serializer = ThirdPartySerializer(data=data)
        if serializer.is_valid():
            third_party = serializer.save()
            application.third_parties.add(str(third_party.id))
            application.save()

            return JsonResponse(data={'third_party': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class RemoveApplicationUltimateEndUser(APIView):
    authentication_classes = (ExporterAuthentication,)

    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_user_type(ExporterUser)
    def delete(self, request, application, ueu_pk):
        """
        Delete an ultimate end user and remove it from the application
        """
        try:
            ultimate_end_user = UltimateEndUser.objects.get(id=ueu_pk)
        except UltimateEndUser.DoesNotExist:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        if ultimate_end_user.organisation != request.user.organisation:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        application.ultimate_end_users.remove(str(ultimate_end_user.id))
        application.save()
        ultimate_end_user.delete()

        return JsonResponse(data={'ultimate_end_user': 'deleted'})


class RemoveThirdParty(APIView):
    authentication_classes = (ExporterAuthentication,)

    @only_application_type(ApplicationLicenceType.STANDARD_LICENCE)
    @authorised_user_type(ExporterUser)
    def delete(self, request, application, tp_pk):
        """
        Delete a third party and remove it from the application
        """
        try:
            third_party = ThirdParty.objects.get(pk=tp_pk)
        except ThirdParty.DoesNotExist:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        if third_party.organisation != request.user.organisation:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        application.third_parties.remove(str(third_party.id))
        application.save()
        third_party.delete()

        return JsonResponse(data={'third_party': 'deleted'})
