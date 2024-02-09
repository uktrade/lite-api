from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView

from api.core.authentication import GovAuthentication, ExporterAuthentication
from api.survey.models import Survey
from api.survey.serializers import SurveySerializer
from api.conf.pagination import MaxPageNumberPagination


# Create your views here.
class SurveyListCreateAPIView(ListCreateAPIView):
    authentication_classes = (GovAuthentication, ExporterAuthentication)
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    pagination_class = MaxPageNumberPagination


class SurveyDetailUpdateAPIView(RetrieveUpdateAPIView):
    authentication_classes = (GovAuthentication, ExporterAuthentication)
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
