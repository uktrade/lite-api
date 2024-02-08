from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from api.core.authentication import GovAuthentication
from api.survey.models import Survey
from api.survey.serializers import SurveySerializer
from api.conf.pagination import MaxPageNumberPagination


# Create your views here.
class SurveyListCreateAPIView(ListCreateAPIView):
    authentication_classes = (GovAuthentication,)
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    pagination_class = MaxPageNumberPagination


class SurveyDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    authentication_classes = (GovAuthentication,)
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
