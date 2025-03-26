from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.response import Response

from api.applications.libraries.get_applications import get_application
from api.core.authentication import GovAuthentication
from api.core.exceptions import NotFoundError

from api.f680.models import Recommendation, SecurityReleaseOutcome
from api.f680.caseworker import filters
from api.f680.caseworker import permissions
from api.f680.caseworker import serializers
from api.f680.caseworker import read_only_serializers


class F680RecommendationViewSet(viewsets.ModelViewSet):
    authentication_classes = (GovAuthentication,)
    permission_classes = (permissions.CaseCanAcceptRecommendations, permissions.CaseCanUserMakeRecommendations)
    filter_backends = (filters.CurrentCaseFilter,)
    queryset = Recommendation.objects.all()
    serializer_class = serializers.F680RecommendationSerializer
    pagination_class = None

    def dispatch(self, request, *args, **kwargs):
        try:
            self.application = get_application(self.kwargs["pk"])
        except (ObjectDoesNotExist, NotFoundError):
            raise Http404()

        return super().dispatch(request, *args, **kwargs)

    def get_case(self):
        return self.application

    def prepare_data(self, request_data):
        return [
            {
                "case": self.kwargs["pk"],
                "user": str(self.request.user.id),
                "team": str(self.request.user.govuser.team.id),
                **item,
            }
            for item in request_data
        ]

    def create(self, request, *args, **kwargs):
        data = self.prepare_data(request.data.copy())
        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = read_only_serializers.F680RecommendationViewSerializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        qs = self.get_queryset().filter(user_id=user.id, team=user.govuser.team)
        if qs.exists:
            qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class F680OutcomeViewSet(viewsets.ModelViewSet):
    authentication_classes = (GovAuthentication,)
    permission_classes = (permissions.CaseReadyForOutcome, permissions.CanUserMakeOutcome)
    filter_backends = (filters.CurrentCaseFilter,)
    queryset = SecurityReleaseOutcome.objects.all()
    serializer_class = serializers.SecurityReleaseOutcomeSerializer
    lookup_url_kwarg = "outcome_id"
    pagination_class = None

    def dispatch(self, request, *args, **kwargs):
        try:
            self.application = get_application(self.kwargs["pk"])
        except (ObjectDoesNotExist, NotFoundError):
            raise Http404()

        return super().dispatch(request, *args, **kwargs)

    def get_case(self):
        return self.application

    def prepare_data(self, request_data):
        return {
            "case": self.kwargs["pk"],
            "user": str(self.request.user.id),
            "team": str(self.request.user.govuser.team.id),
            **request_data,
        }

    def create(self, request, *args, **kwargs):
        data = self.prepare_data(request.data.copy())
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
