import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.libraries.get_ultimate_end_users import get_ultimate_end_users
from conf.authentication import ExporterAuthentication
from drafts.libraries.get_draft import get_draft
from end_user.document.models import EndUserDocument
from end_user.models import EndUser
from end_user.serializers import EndUserSerializer
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
                end_user = serializer.save()

                # Reversion
                reversion.set_user(request.user)
                reversion.set_comment('Created End User')

                # Ensure previous end_user on same draft is deleted when submitting a new one
                if draft.end_user:
                    old_end_user = EndUser.objects.get(id=draft.end_user.id)
                    old_end_user_document = EndUserDocument.objects.filter(end_user__id=draft.end_user.id).first()
                    if old_end_user_document:
                        old_end_user_document.delete_s3()
                    old_end_user.delete()

                # Set the end user of the draft application
                draft.end_user = end_user
                draft.save()

                return JsonResponse(data={'end_user': serializer.data},
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

        serializer = EndUserSerializer(ultimate_end_users, many=True)

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
            serializer = EndUserSerializer(data=data)
            if serializer.is_valid():
                end_user = serializer.save()

                # Reversion
                reversion.set_user(request.user)
                reversion.set_comment("Created End User")

                # Set the end user of the draft application
                draft.ultimate_end_users.add(str(end_user.id))

                draft.save()

                return JsonResponse(data={'end_user': serializer.data},
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
        draft = get_draft(pk)
        try:
            end_user = EndUser.objects.get(id=ueu_pk)
            if end_user.organisation != organisation:
                return JsonResponse(data={'errors': 'request invalid'},
                                    status=400)
        except EndUser.DoesNotExist:
            return JsonResponse(data={'errors': 'request invalid'},
                                status=400)

        with reversion.create_revision():
            # Reversion
            reversion.set_user(request.user)
            reversion.set_comment("Deleted End User")

            # Set the end user of the draft application
            draft.ultimate_end_users.remove(str(end_user.id))
            draft.save()

            end_user.delete()

            return JsonResponse(data={'ultimate_end_user': 'deleted'},
                                status=200)
