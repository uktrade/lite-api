import reversion
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from drafts.libraries.get_draft import get_draft_with_organisation
from drafts.models import Draft
from drafts.serializers import DraftBaseSerializer, DraftCreateSerializer, DraftUpdateSerializer
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
        return JsonResponse(data={'drafts': serializer.data})

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
