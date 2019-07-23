import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from drafts.libraries.get_draft import get_draft
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
