from django.http import JsonResponse
from rest_framework.views import APIView

from api.core.authentication import GovAuthentication
from api.staticdata.report_summaries.helpers import filtered_ordered_queryset
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from api.staticdata.report_summaries.serializers import ReportSummaryPrefixSerializer, ReportSummarySubjectSerializer


class ReportSummaryPrefixView(APIView):
    authentication_classes = (GovAuthentication,)

    def get_queryset(self):
        part_of_name = self.request.GET.get("name")
        model_class = ReportSummaryPrefix
        prefixes = filtered_ordered_queryset(model_class, part_of_name)
        return prefixes

    def get(self, request):
        """
        Returns report summary prefixes
        """
        prefix_serializer = ReportSummaryPrefixSerializer(self.get_queryset(), many=True)
        return JsonResponse(data={"report_summary_prefixes": prefix_serializer.data})


class ReportSummarySubjectView(APIView):
    authentication_classes = (GovAuthentication,)

    def get_queryset(self):
        part_of_name = self.request.GET.get("name")
        model_class = ReportSummarySubject
        prefixes = filtered_ordered_queryset(model_class, part_of_name)
        return prefixes

    def get(self, request):
        """
        Returns report summary subjects
        """
        subject_serializer = ReportSummarySubjectSerializer(self.get_queryset(), many=True)
        return JsonResponse(data={"report_summary_subjects": subject_serializer.data})
