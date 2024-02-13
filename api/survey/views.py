from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView

from api.core.authentication import ExporterAuthentication
from api.survey.models import SurveyResponse
from api.survey.serializers import SurveyResponseSerializer


class SurveyCreateAPIView(CreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    queryset = SurveyResponse.objects.all()
    serializer_class = SurveyResponseSerializer


class SurveyDetailUpdateAPIView(RetrieveUpdateAPIView):
    authentication_classes = (ExporterAuthentication,)
    queryset = SurveyResponse.objects.all()
    serializer_class = SurveyResponseSerializer
