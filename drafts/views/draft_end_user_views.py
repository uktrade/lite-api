import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.libraries.get_ultimate_end_users import get_ultimate_end_users
from conf.authentication import ExporterAuthentication
from drafts.libraries.get_draft import get_draft
from parties.helpers import delete_end_user_document_if_exists
from parties.models import Party, EndUser, UltimateEndUser
from parties.serializers import PartySerializer, EndUserSerializer, UltimateEndUserSerializer
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
        data['draft'] = draft

        with reversion.create_revision():
            serializer = EndUserSerializer(data=data)
            if serializer.is_valid():
                serializer.save()

                # Reversion
                reversion.set_user(request.user)
                reversion.set_comment('Created End User')

                # Delete previous end user and its document
                old_end_user = EndUser.objects.filter(draft=draft)
                delete_end_user_document_if_exists(old_end_user)
                old_end_user.delete()

                return JsonResponse(data={'parties': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)


class DraftUltimateEndUsers(APIView):
    """
    Set and remove ultimate end users from the draft
    """
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Get ultimate end users associated with a draft
        """
        draft = get_draft(pk)
        ultimate_end_users = get_ultimate_end_users(draft)

        serializer = UltimateEndUserSerializer(ultimate_end_users, many=True)

        return JsonResponse(data={'ultimate_end_users': serializer.data})

    def post(self, request, pk):
        """
        Create and add an ultimate end user to a draft
        """
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        data['organisation'] = str(organisation.id)
        data['draft'] = get_draft(pk)

        with reversion.create_revision():
            serializer = UltimateEndUserSerializer(data=data)
            if serializer.is_valid():
                serializer.save()

                # Reversion
                reversion.set_user(request.user)
                reversion.set_comment("Created End User")

                return JsonResponse(data={'parties': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)


class RemoveDraftUltimateEndUsers(APIView):
    """
    Remove ultimate end users from a draft and delete the record (deletion won't happen in the future)
    """
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    def delete(self, request, pk, ueu_pk):
        """
        delete the ultimate end user from the draft
        """
        organisation = get_organisation_by_user(request.user)
        try:
            ultimate_end_user = UltimateEndUser.objects.get(pk=ueu_pk)
            if ultimate_end_user.organisation != organisation:
                return JsonResponse(data={'errors': 'request invalid'},
                                    status=400)
            else:
                with reversion.create_revision():
                    # Reversion
                    reversion.set_user(request.user)
                    reversion.set_comment("Deleted End User")

                    return JsonResponse(data={'ultimate_end_user': 'deleted'},
                                        status=200)
        except UltimateEndUser.DoesNotExist:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)
