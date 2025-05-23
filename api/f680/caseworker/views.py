from django.http import HttpResponse
from api.cases.generated_documents.models import GeneratedCaseDocument
from rest_framework import status, viewsets
from rest_framework.response import Response

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.libraries.get_case import get_case

from api.f680.models import Recommendation, SecurityReleaseOutcome
from api.f680.caseworker import permissions
from api.f680.caseworker import serializers
from api.f680.caseworker import read_only_serializers
from api.f680.caseworker.mixins import F680CaseworkerApplicationMixin


class F680RecommendationViewSet(F680CaseworkerApplicationMixin, viewsets.ModelViewSet):
    permission_classes = [
        permissions.CaseCanAcceptRecommendations & permissions.CaseCanUserMakeRecommendations | permissions.ReadOnly
    ]
    serializer_class = serializers.F680RecommendationSerializer
    pagination_class = None
    queryset = Recommendation.objects.all()

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
        serializer.save()

        recommendation_type = serializer.data[0]["type"]["value"]
        qs = self.get_queryset().filter(user_id=request.user.id, team=request.user.govuser.team)
        security_release_request_ids = [str(item.security_release_request.id) for item in qs]

        audit_trail_service.create(
            actor=self.request.user,
            verb=AuditType.CREATE_OGD_F680_RECOMMENDATION,
            target=self.case,
            payload={
                "security_release_request_ids": security_release_request_ids,
                "additional_text": f"Recommendation type added was {recommendation_type}",
            },
        )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = read_only_serializers.F680RecommendationViewSerializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(user_id=request.user.id, team=request.user.govuser.team)
        security_release_request_ids = [str(item.security_release_request.id) for item in qs]

        if qs.exists:
            qs.delete()

        audit_trail_service.create(
            actor=self.request.user,
            verb=AuditType.CLEAR_OGD_F680_RECOMMENDATION,
            target=get_case(self.kwargs["pk"]),
            payload={"security_release_request_ids": security_release_request_ids},
        )

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class F680OutcomeViewSet(F680CaseworkerApplicationMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.CanUserMakeOutcome & permissions.CaseReadyForOutcome | permissions.ReadOnly]
    queryset = SecurityReleaseOutcome.objects.all()
    serializer_class = serializers.SecurityReleaseOutcomeSerializer
    lookup_url_kwarg = "outcome_id"
    pagination_class = None

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

        outcome = serializer.data["outcome"]
        security_release_request_ids = [str(item) for item in serializer.data["security_release_requests"]]

        audit_trail_service.create(
            actor=self.request.user,
            verb=AuditType.CREATE_F680_OUTCOME,
            target=self.case,
            payload={
                "security_release_request_ids": security_release_request_ids,
                "additional_text": f"Outcome was {outcome}",
                "security_grading": serializer.data["security_grading"],
            },
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        security_release_request_ids = [str(item.id) for item in self.get_object().security_release_requests.all()]

        response = super().destroy(request, *args, **kwargs)

        audit_trail_service.create(
            actor=self.request.user,
            verb=AuditType.CLEAR_F680_OUTCOME,
            target=self.case,
            payload={
                "security_release_request_ids": security_release_request_ids,
            },
        )
        # The following makes 204 no content responses play nicely with hawk authentication
        return HttpResponse(status=response.status_code)


class F680OutcomeDocumentViewSet(F680CaseworkerApplicationMixin, viewsets.ModelViewSet):
    queryset = GeneratedCaseDocument.objects.all()
    serializer_class = serializers.OutcomeDocumentSerializer
    lookup_url_kwarg = "case_id"
    pagination_class = None
