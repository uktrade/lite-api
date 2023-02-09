from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from rest_framework import serializers


class ReportSummaryPrefixSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSummaryPrefix
        fields = (
            "id",
            "name",
        )


class ReportSummarySubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSummarySubject
        fields = (
            "id",
            "name",
        )
