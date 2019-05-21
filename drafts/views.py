import reversion
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from drafts.libraries.get_draft import get_draft_with_organisation, get_good_with_organisation
from drafts.models import Draft, GoodOnDraft
from drafts.serializers import DraftBaseSerializer, DraftCreateSerializer, DraftUpdateSerializer, \
    GoodOnDraftBaseSerializer, GoodOnDraftViewSerializer
from organisations.libraries.get_organisation import get_organisation_by_user


class DraftList(APIView):
    authentication_classes = (PkAuthentication,)
    """
    List all drafts that belong to an organisation create a new draft.
    """
    def get(self, request):
        organisation = get_organisation_by_user(request.user)

        drafts = Draft.objects.filter(organisation=organisation).order_by('-created_at')
        serializer = DraftBaseSerializer(drafts, many=True)
        return JsonResponse(data={'drafts': serializer.data},
                            safe=False)

    def post(self, request):
        organisation = get_organisation_by_user(request.user)
        data = request.data
        data['organisation'] = str(organisation.id)

        serializer = DraftCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'draft': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class DraftDetail(APIView):
    authentication_classes = (PkAuthentication,)
    """
    Retrieve, update or delete a draft instance.
    """
    def get(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        draft = get_draft_with_organisation(pk, organisation)
        serializer = DraftBaseSerializer(draft)
        return JsonResponse(data={'draft': serializer.data})

    def put(self, request, pk):
        organisation = get_organisation_by_user(request.user)

        with reversion.create_revision():
            serializer = DraftUpdateSerializer(get_draft_with_organisation(pk, organisation),
                                               data=request.data,
                                               partial=True)
            if serializer.is_valid():
                serializer.save()

                # Store version meta-information
                reversion.set_user(request.user)
                reversion.set_comment("Created Draft Revision")

                return JsonResponse(data={'draft': serializer.data},
                                    status=status.HTTP_200_OK)
            return JsonResponse(data={'errors': serializer.errors},
                                status=400)

    def delete(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        draft = get_draft_with_organisation(pk, organisation)
        draft.delete()
        return JsonResponse(data={'status': 'Draft Deleted'},
                            status=status.HTTP_200_OK)


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
        return JsonResponse(data={'goods': serializer.data},
                            safe=False)

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

