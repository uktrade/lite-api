import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from drafts.libraries.get_draft import get_draft
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
                reversion.set_comment("Created End User")

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
                                status=400)

    @transaction.atomic
    def delete(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        draft = get_draft(pk)
        try:
            end_user = EndUser.objects.get(id=data['id'])
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
