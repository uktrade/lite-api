from django.http import JsonResponse
from rest_framework.views import APIView

from api.core.authentication import GovAuthentication
from api.staticdata.report_summaries.helpers import filter_and_order_by_name
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from api.staticdata.report_summaries.serializers import ReportSummaryPrefixSerializer, ReportSummarySubjectSerializer


class ReportSummaryPrefixesListView(APIView):
    authentication_classes = (GovAuthentication,)

    def get_queryset(self):
        part_of_name = self.request.GET.get("name")
        return filter_and_order_by_name(ReportSummaryPrefix.objects.all(), part_of_name)

    def get(self, request):
        """
        Returns report summary prefixes
        """
        prefix_serializer = ReportSummaryPrefixSerializer(self.get_queryset(), many=True)
        return JsonResponse(data={"report_summary_prefixes": prefix_serializer.data})


class ReportSummarySubjectsListView(APIView):
    authentication_classes = (GovAuthentication,)

    def get_queryset(self):
        part_of_name = self.request.GET.get("name")
        return filter_and_order_by_name(ReportSummarySubject.objects.all(), part_of_name)

    def get(self, request):
        """
        Returns report summary subjects
        """
        subject_serializer = ReportSummarySubjectSerializer(self.get_queryset(), many=True)
        return JsonResponse(data={"report_summary_subjects": subject_serializer.data})
