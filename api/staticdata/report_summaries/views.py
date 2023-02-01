from django.http import JsonResponse
from rest_framework.views import APIView

from api.core.authentication import SharedAuthentication
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from api.staticdata.report_summaries.serializers import ReportSummaryPrefixSerializer, ReportSummarySubjectSerializer


class ReportSummaryPrefixView(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        """
        Returns report summary prefixes
        """
        prefixes = ReportSummaryPrefixSerializer(ReportSummaryPrefix.objects.all(), many=True).data
        return JsonResponse(data={"report_summary_prefixes": prefixes})


class ReportSummarySubjectView(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        """
        Returns report summary subjects
        """
        subjects = ReportSummarySubjectSerializer(ReportSummarySubject.objects.all(), many=True).data
        return JsonResponse(data={"report_summary_subjects": subjects})
