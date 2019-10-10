from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from applications.libraries.get_applications import get_application
from conf.authentication import ExporterAuthentication
from conf.decorators import only_application_types
from parties.helpers import delete_party_document_if_exists
from parties.models import UltimateEndUser, ThirdParty
from parties.serializers import EndUserSerializer, UltimateEndUserSerializer, ConsigneeSerializer, ThirdPartySerializer


class ApplicationEndUser(APIView):
    authentication_classes = (ExporterAuthentication,)

    @only_application_types(ApplicationLicenceType.STANDARD_LICENCE)
    def post(self, request, draft):
        """
        Create an end user and add it to a draft
        """
        data = request.data
        data['organisation'] = str(request.user.organisation.id)

        serializer = EndUserSerializer(data=data)
        if serializer.is_valid():
            previous_end_user = draft.end_user

            new_end_user = serializer.save()
            draft.end_user = new_end_user
            draft.save()

            if previous_end_user:
                delete_party_document_if_exists(previous_end_user)
                previous_end_user.delete()

            return JsonResponse(data={'end_user': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class ApplicationUltimateEndUsers(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Get ultimate end users associated with a draft
        """
        draft = get_application(pk, organisation_id=request.user.organisation.id)
        ueu_data = []

        if draft.licence_type == ApplicationLicenceType.STANDARD_LICENCE:
            ueu_data = UltimateEndUserSerializer(draft.ultimate_end_users, many=True).data

        return JsonResponse(data={'ultimate_end_users': ueu_data})

    @only_application_types(ApplicationLicenceType.STANDARD_LICENCE)
    def post(self, request, draft):
        """
        Create an ultimate end user and add it to a draft
        """
        data = request.data
        data['organisation'] = str(request.user.organisation.id)

        serializer = UltimateEndUserSerializer(data=data)
        if serializer.is_valid():
            ultimate_end_user = serializer.save()
            draft.ultimate_end_users.add(str(ultimate_end_user.id))
            draft.save()

            return JsonResponse(data={'ultimate_end_user': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class ApplicationConsignee(APIView):
    authentication_classes = (ExporterAuthentication,)

    @only_application_types(ApplicationLicenceType.STANDARD_LICENCE)
    def post(self, request, draft):
        """
        Create a consignee and add it to a draft
        """
        data = request.data
        data['organisation'] = str(request.user.organisation.id)

        serializer = ConsigneeSerializer(data=data)
        if serializer.is_valid():
            previous_consignee = draft.consignee

            new_consignee = serializer.save()
            draft.consignee = new_consignee
            draft.save()

            if previous_consignee:
                delete_party_document_if_exists(previous_consignee)
                previous_consignee.delete()

            return JsonResponse(data={'consignee': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class ApplicationThirdParties(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Get third parties associated with a draft
        """
        draft = get_application(pk, organisation_id=request.user.organisation.id)
        third_party_data = []

        if draft.licence_type == ApplicationLicenceType.STANDARD_LICENCE:
            third_party_data = ThirdPartySerializer(draft.third_parties, many=True).data

        return JsonResponse(data={'third_parties': third_party_data})

    @only_application_types(ApplicationLicenceType.STANDARD_LICENCE)
    def post(self, request, draft):
        """
        Create a third party and add it to a draft
        """
        data = request.data
        data['organisation'] = str(request.user.organisation.id)

        serializer = ThirdPartySerializer(data=data)
        if serializer.is_valid():
            third_party = serializer.save()
            draft.third_parties.add(str(third_party.id))
            draft.save()

            return JsonResponse(data={'third_party': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class RemoveApplicationUltimateEndUser(APIView):
    authentication_classes = (ExporterAuthentication,)

    def delete(self, request, pk, ueu_pk):
        """
        Delete an ultimate end user and remove it from the draft
        """
        draft = get_application(pk)

        try:
            ultimate_end_user = UltimateEndUser.objects.get(id=ueu_pk)
        except UltimateEndUser.DoesNotExist:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        if ultimate_end_user.organisation != request.user.organisation:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        draft.ultimate_end_users.remove(str(ultimate_end_user.id))
        draft.save()
        ultimate_end_user.delete()

        return JsonResponse(data={'ultimate_end_user': 'deleted'})


class RemoveThirdParty(APIView):
    authentication_classes = (ExporterAuthentication,)

    def delete(self, request, pk, tp_pk):
        """
        Delete a third party and remove it from the draft
        """
        draft = get_application(pk)

        try:
            third_party = ThirdParty.objects.get(pk=tp_pk)
        except ThirdParty.DoesNotExist:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        if third_party.organisation != request.user.organisation:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        draft.third_parties.remove(str(third_party.id))
        draft.save()
        third_party.delete()

        return JsonResponse(data={'third_party': 'deleted'})
