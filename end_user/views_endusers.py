import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from end_user.models import EndUser
from end_user.serializers import EndUserViewSerializer, EndUserCreateSerializer, EndUserUpdateSerializer
from organisations.libraries.get_organisation import get_organisation_by_user, get_organisation_by_pk
from organisations.libraries.get_site import get_site_with_organisation
from organisations.models import Organisation, Site

from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.libraries.get_site import get_site_with_organisation
from organisations.serializers import SiteViewSerializer, SiteCreateSerializer, SiteUpdateSerializer


class OrgEndUserList(APIView):
    """
    List all sites for an organisation/create site
    """

    def get(self, request, org_pk):
        """
        Endpoint for listing the Sites of an organisation
        An organisation must have at least one site
        """

        end_users = EndUser.objects.filter(organisation=org_pk)
        serializer = EndUserViewSerializer(end_users, many=True)
        return JsonResponse(data={'end_users': serializer.data},
                            safe=False)

    @transaction.atomic
    def post(self, request, org_pk):
        with reversion.create_revision():
            organisation = Organisation.objects.get(pk=org_pk)
            data = JSONParser().parse(request)
            data['organisation'] = organisation.id
            serializer = EndUserCreateSerializer(data=data)

            if serializer.is_valid():
                # user information for gov users does not exist yet
                # reversion.set_user(request.user)
                # reversion.set_comment("Created EndUser")
                return JsonResponse(data={'end_user': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrgEndUserDetail(APIView):
    """
    Show details for for a specific site/edit site
    """

    def get(self, request, org_pk, end_user_pk):
        # organisation = get_organisation_by_user(request.user)
        organisation = Organisation.objects.get(pk=org_pk)
        site = EndUser.objects.get(pk=end_user_pk)

        serializer = EndUserViewSerializer(site)
        return JsonResponse(data={'end_user': serializer.data},
                            safe=False)

    @transaction.atomic
    def put(self, request, org_pk, end_user_pk):
        # organisation = get_organisation_by_user(request.user)
        organisation = Organisation.objects.get(pk=org_pk)
        site = EndUser.objects.get(pk=end_user_pk)

        with reversion.create_revision():
            serializer = EndUserUpdateSerializer(site,
                                                 data=request.data,
                                                 partial=True)
            if serializer.is_valid():
                serializer.save()
                # user information for gov users does not exist yet
                # reversion.set_user(request.user)
                # reversion.set_comment("Created Site Revision")

                return JsonResponse(data={'end_user': serializer.data},
                                    status=status.HTTP_200_OK)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)
