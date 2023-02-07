from django.db.models import BinaryField, Case, When
from django.http import JsonResponse
from rest_framework.views import APIView

from api.core.authentication import GovAuthentication
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from api.staticdata.report_summaries.serializers import ReportSummaryPrefixSerializer, ReportSummarySubjectSerializer


def filtered_ordered_queryset(model_class, part_of_name):
    """
    Creates a queryset to get rows for the model where the
    'name' column contains the part_of_name parameter. The results
    are sorted so that entries where the name is prefixed by
    the part_of_name appear higher in the rankings and
    alphabetically after that.
    """
    queryset = model_class.objects.all()
    if part_of_name:
        queryset = queryset.filter(name__icontains=part_of_name)
        queryset = queryset.annotate(
            is_prefixed=Case(
                When(name__istartswith=part_of_name.lower(), then=True),
                default=False,
                output_field=BinaryField(),
            ),
        )
        queryset = queryset.order_by("-is_prefixed", "name")
    return queryset


class ReportSummaryPrefixView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Returns report summary prefixes
        """
        part_of_name = self.request.GET.get("name")
        model_class = ReportSummaryPrefix
        prefixes = filtered_ordered_queryset(model_class, part_of_name)
        prefix_serializer = ReportSummaryPrefixSerializer(prefixes, many=True)
        return JsonResponse(data={"report_summary_prefixes": prefix_serializer.data})


class ReportSummarySubjectView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Returns report summary subjects
        """
        part_of_name = self.request.GET.get("name")
        model_class = ReportSummarySubject
        subjects = filtered_ordered_queryset(model_class, part_of_name)
        subject_serializer = ReportSummarySubjectSerializer(subjects, many=True)
        return JsonResponse(data={"report_summary_subjects": subject_serializer.data})
