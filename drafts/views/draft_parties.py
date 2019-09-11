import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from drafts.libraries.get_draft import get_draft
from parties.helpers import delete_end_user_document_if_exists
from parties.models import UltimateEndUser
from parties.serializers import EndUserSerializer, UltimateEndUserSerializer, ConsigneeSerializer, ThirdPartySerializer
from organisations.libraries.get_organisation import get_organisation_by_user


class DraftEndUser(APIView):
    """
    Set the end user of a draft application
    """
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    def post(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        draft = get_draft(pk)
        data['organisation'] = str(organisation.id)

        with reversion.create_revision():
            serializer = EndUserSerializer(data=data)
            if serializer.is_valid():
                new_end_user = serializer.save()

                # Reversion
                reversion.set_user(request.user)
                reversion.set_comment('Created End User')

                # Delete previous end user and its document
                if draft.end_user:
                    delete_end_user_document_if_exists(draft.end_user)
                    draft.end_user.delete()

                # Set the end user of the draft application
                draft.end_user = new_end_user
                draft.save()

                return JsonResponse(data={'end_user': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errodrafts/urls.pyrs': serializer.errors},
                                status=400)


class DraftUltimateEndUsers(APIView):
    """
    Set/Get ultimate end users to/from a draft
    """
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Get ultimate end users associated with a draft
        """
        draft = get_draft(pk)

        serializer = UltimateEndUserSerializer(draft.ultimate_end_users, many=True)
        return JsonResponse(data={'ultimate_end_users': serializer.data})

    def post(self, request, pk):
        """
        Create and add an ultimate end user to a draft
        """
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        draft = get_draft(pk)
        data['organisation'] = str(organisation.id)

        with reversion.create_revision():
            serializer = UltimateEndUserSerializer(data=data)
            if serializer.is_valid():
                ultimate_end_user = serializer.save()

                # Reversion
                reversion.set_user(request.user)
                reversion.set_comment("Created End User")

                # Set the end user of the draft application
                draft.ultimate_end_users.add(str(ultimate_end_user.id))

                draft.save()

                return JsonResponse(data={'end_user': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)


class RemoveDraftUltimateEndUser(APIView):
    """
    Remove an ultimate end user from a draft and delete the record (deletion won't happen in the future)
    """
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    def delete(self, request, pk, ueu_pk):
        """
        delete the ultimate end user from the draft
        """
        organisation = get_organisation_by_user(request.user)
        draft = get_draft(pk)
        try:
            ultimate_end_user = UltimateEndUser.objects.get(id=ueu_pk)
            if ultimate_end_user.organisation != organisation:
                return JsonResponse(data={'errors': 'request invalid'},
                                    status=400)
        except UltimateEndUser.DoesNotExist:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        with reversion.create_revision():
            # Reversion
            reversion.set_user(request.user)
            reversion.set_comment("Deleted End User")

            # Set the end user of the draft application
            draft.ultimate_end_users.remove(str(ultimate_end_user.id))
            draft.save()

            ultimate_end_user.delete()

            return JsonResponse(data={'ultimate_end_user': 'deleted'})


class DraftConsignee(APIView):
    """
    Set the consignee of a draft application
    """
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    def post(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        draft = get_draft(pk)
        data['organisation'] = str(organisation.id)

        with reversion.create_revision():
            serializer = ConsigneeSerializer(data=data)
            if serializer.is_valid():
                new_consignee = serializer.save()

                # Reversion
                reversion.set_user(request.user)
                reversion.set_comment('Created Consignee User')

                # Delete previous consignee
                if draft.new_consignee:
                    draft.new_consignee.delete()

                # Set the end user of the draft application
                draft.consignee = new_consignee
                draft.save()

                return JsonResponse(data={'consignee': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)


class DraftThirdParties(APIView):
    """
    Set the third parties of a draft application
    """
    authentication_classes = (ExporterAuthentication,)

    def post(self, request, pk):
        """
        Create and add a third party to a draft
        """
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        draft = get_draft(pk)
        data['organisation'] = str(organisation.id)

        with reversion.create_revision():
            serializer = ThirdPartySerializer(data=data)
            if serializer.is_valid():
                third_party = serializer.save()

                # Reversion
                reversion.set_user(request.user)
                reversion.set_comment("Created Third Party")

                # Set the end user of the draft application
                draft.third_parties.add(str(third_party.id))

                draft.save()

                return JsonResponse(data={'third_party': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
