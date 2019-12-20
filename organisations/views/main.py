import operator
from functools import reduce

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics

from conf.authentication import SharedAuthentication
from organisations.models import Organisation
from organisations.serializers import OrganisationDetailSerializer, OrganisationCreateSerializer


class OrganisationsList(generics.ListCreateAPIView):
    authentication_classes = (SharedAuthentication,)
    serializer_class = OrganisationDetailSerializer

    def get_queryset(self):
        """
        List all organisations
        """
        org_types = self.request.query_params.getlist("org_type", [])
        search_term = self.request.query_params.get("search_term", "")

        query = [Q(name__icontains=search_term) | Q(registration_number__icontains=search_term)]

        result = Organisation.objects.filter(reduce(operator.and_, query)).order_by("name")

        if org_types:
            result = result.filter(Q(type__in=org_types))

        return result

    @transaction.atomic
    @swagger_auto_schema(request_body=OrganisationCreateSerializer, responses={400: "JSON parse error"})
    def post(self, request):
        """
        Create a new organisation
        """
        serializer = OrganisationCreateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data=serializer.data, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class OrganisationsDetail(generics.RetrieveAPIView):
    authentication_classes = (SharedAuthentication,)
    queryset = Organisation.objects.all()
    serializer_class = OrganisationDetailSerializer
