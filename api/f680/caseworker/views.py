from rest_framework import status, viewsets
from rest_framework.response import Response

from api.core.authentication import GovAuthentication

from api.f680.models import Recommendation
from api.f680.caseworker.serializers import F680RecommendationSerializer


class F680RecommendationViewSet(viewsets.ModelViewSet):
    authentication_classes = (GovAuthentication,)
    serializer_class = F680RecommendationSerializer
    queryset = Recommendation.objects.all()
    pagination_class = None

    def delete_user_recommendation(self):
        current_user = self.request.user
        qs = Recommendation.objects.filter(
            case_id=self.kwargs["pk"], user_id=current_user.id, team=current_user.govuser.team
        )
        if qs.exists:
            qs.delete()

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

        self.delete_user_recommendation()
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
