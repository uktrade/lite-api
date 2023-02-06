from django.db.models import BinaryField, Case, When
from django.http import JsonResponse
from rest_framework.views import APIView

from api.core.authentication import GovAuthentication
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from api.staticdata.report_summaries.serializers import ReportSummaryPrefixSerializer, ReportSummarySubjectSerializer


class ReportSummaryPrefixView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Returns report summary prefixes
        """
        name = self.request.GET.get("name")
        prefixes = ReportSummaryPrefix.objects.all()

        if name:
            prefixes = prefixes.filter(name__icontains=name)
            prefixes = prefixes.annotate(
                is_prefixed=Case(
                    When(name__istartswith=name.lower(), then=True),
                    default=False,
                    output_field=BinaryField(),
                ),
            )
            prefixes = prefixes.order_by("-is_prefixed", "name")

        prefix_serializer = ReportSummaryPrefixSerializer(prefixes, many=True)
        return JsonResponse(data={"report_summary_prefixes": prefix_serializer.data})


class ReportSummarySubjectView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Returns report summary subjects
        """
        subjects = ReportSummarySubjectSerializer(ReportSummarySubject.objects.all(), many=True).data
        return JsonResponse(data={"report_summary_subjects": subjects})
