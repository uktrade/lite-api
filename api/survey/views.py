from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView

from api.core.authentication import ExporterAuthentication
from api.survey.models import SurveyResponse
from api.survey.serializers import SurveySerializer
from api.conf.pagination import MaxPageNumberPagination


# Create your views here.
class SurveyCreateAPIView(CreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    queryset = SurveyResponse.objects.all()
    serializer_class = SurveySerializer


class SurveyDetailUpdateAPIView(RetrieveUpdateAPIView):
    authentication_classes = (ExporterAuthentication,)
    queryset = SurveyResponse.objects.all()
    serializer_class = SurveySerializer
