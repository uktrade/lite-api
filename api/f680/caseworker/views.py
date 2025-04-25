from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from rest_framework import status, viewsets
from rest_framework.response import Response

from api.applications.libraries.get_applications import get_application
from api.audit_trail.enums import AuditType
from api.core.authentication import GovAuthentication
from api.core.exceptions import NotFoundError

from api.f680.models import Recommendation, SecurityReleaseOutcome
from api.f680.caseworker import filters
from api.f680.caseworker import permissions
from api.f680.caseworker import serializers
from api.f680.caseworker import read_only_serializers


class F680RecommendationViewSet(viewsets.ModelViewSet):
    authentication_classes = (GovAuthentication,)
    permission_classes = [
        permissions.CaseCanAcceptRecommendations & permissions.CaseCanUserMakeRecommendations | permissions.ReadOnly
    ]
    filter_backends = (filters.CurrentCaseFilter,)
    queryset = Recommendation.objects.all()
    serializer_class = serializers.F680RecommendationSerializer
    pagination_class = None

    def dispatch(self, request, *args, **kwargs):
        # TODO: Review dispatch methods in LTD-6085
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

    def create_audit(self, audit_type, recommendation_type=None, payload=None):
        from api.audit_trail import service as audit_trail_service

        if recommendation_type:
            payload.update({"additional_text": f"With advice type of {recommendation_type}"})

        audit_trail_service.create(
            actor=self.request.user,
            verb=audit_type,
            target=self.application.get_case(),
            payload=payload,
        )

    def create(self, request, *args, **kwargs):
        data = self.prepare_data(request.data.copy())
        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        # A record of the security release objects impacted by the recommendation for the audit table
        security_release_request_object_ids = [str(item["security_release_request"]) for item in serializer.data]
        # Recommendation  type records will all be the same type as serializer does not allowed mixed advice
        recommendation_type = serializer.data[0]["type"]["value"]
        self.create_audit(
            audit_type=AuditType.CREATE_OGD_F680_RECOMMENDATION,
            advice_type=recommendation_type,
            payload={"security_release_request_object_ids": security_release_request_object_ids},
        )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = read_only_serializers.F680RecommendationViewSerializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        qs = self.get_queryset().filter(user_id=user.id, team=user.govuser.team)

        # A record for the audit table of the recommendation_object_ids which have been removed
        recommendation_ids = [str(recommendation.id) for recommendation in qs]

        if qs.exists:
            qs.delete()

        self.create_audit(
            audit_type=AuditType.CLEAR_OGD_F680_RECOMMENDATION,
            payload={"recommendation_object_ids": recommendation_ids},
        )
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class F680OutcomeViewSet(viewsets.ModelViewSet):
    authentication_classes = (GovAuthentication,)
    permission_classes = [permissions.CaseReadyForOutcome & permissions.CanUserMakeOutcome | permissions.ReadOnly]
    filter_backends = (filters.CurrentCaseFilter,)
    queryset = SecurityReleaseOutcome.objects.all()
    serializer_class = serializers.SecurityReleaseOutcomeSerializer
    lookup_url_kwarg = "outcome_id"
    pagination_class = None

    def dispatch(self, request, *args, **kwargs):
        # TODO: Review dispatch methods in LTD-6085
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

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        # The following makes 204 no content responses play nicely with hawk authentication
        return HttpResponse(status=response.status_code)
