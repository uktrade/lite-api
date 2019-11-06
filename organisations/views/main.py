import operator
from functools import reduce

import reversion
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from rest_framework.parsers import JSONParser

from conf.authentication import SharedAuthentication
from conf.pagination import MaxPageNumberPagination
from organisations.models import Organisation
from organisations.serializers import (
    OrganisationDetailSerializer,
    OrganisationCreateSerializer,
)


class OrganisationsList(generics.ListAPIView):
    authentication_classes = (SharedAuthentication,)
    serializer_class = OrganisationDetailSerializer
    pagination_class = MaxPageNumberPagination

    def get_queryset(self):
        """
        List all organisations
        """
        org_type = self.request.query_params.get("org_type", None)
        name = self.request.query_params.get("name", "")

        query = [Q(name__icontains=name)]

        if org_type:
            query.append(Q(type=org_type))
        return Organisation.objects.filter(reduce(operator.and_, query)).order_by(
            "name"
        )

    @transaction.atomic
    @swagger_auto_schema(
        request_body=OrganisationCreateSerializer, responses={400: "JSON parse error"}
    )
    def post(self, request):
        """
        Create a new organisation
        """
        with reversion.create_revision():
            data = JSONParser().parse(request)
            if data.get("type") == "individual":
                try:
                    data["name"] = (
                        data["user"]["first_name"] + " " + data["user"]["last_name"]
                    )
                except AttributeError:
                    pass
                except KeyError:
                    pass
            serializer = OrganisationCreateSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse(
                    data={"organisation": serializer.data},
                    status=status.HTTP_201_CREATED,
                )

            return JsonResponse(
                data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )


class OrganisationsDetail(generics.RetrieveAPIView):
    authentication_classes = (SharedAuthentication,)

    queryset = Organisation.objects.all()
    serializer_class = OrganisationDetailSerializer
