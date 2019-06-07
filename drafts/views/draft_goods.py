import reversion
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from drafts.libraries.get_draft import get_draft_with_organisation, get_good_with_organisation
from drafts.models import GoodOnDraft
from drafts.serializers import GoodOnDraftBaseSerializer, GoodOnDraftViewSerializer
from organisations.libraries.get_organisation import get_organisation_by_user


class DraftGoods(APIView):
    authentication_classes = (PkAuthentication,)
    """
    View goods belonging to a draft, or add one
    """
    def get(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        draft = get_draft_with_organisation(pk, organisation)

        goods = GoodOnDraft.objects.filter(draft=draft)
        serializer = GoodOnDraftViewSerializer(goods, many=True)
        return JsonResponse(data={'goods': serializer.data})

    def post(self, request, pk):
        data = JSONParser().parse(request)

        data['good'] = data['good_id']
        data['draft'] = str(pk)

        organisation = get_organisation_by_user(request.user)
        get_draft_with_organisation(pk, organisation)
        get_good_with_organisation(data.get('good'), organisation)

        with reversion.create_revision():
            serializer = GoodOnDraftBaseSerializer(data=data)
            if serializer.is_valid():
                serializer.save()

                reversion.set_user(request.user)
                reversion.set_comment("Created Good on Draft Revision")

                return JsonResponse(data={'good': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)
