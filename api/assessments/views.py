from collections import Counter

from django.db import transaction
from django.http import JsonResponse
from rest_framework import generics, serializers
from rest_framework import status

from api.applications.models import GoodOnApplication, StandardApplication
from api.assessments.serializers import AssessmentSerializer, is_legacy_line_item
from api.core.authentication import GovAuthentication


class MakeAssessmentsView(generics.UpdateAPIView):

    serializer_class = AssessmentSerializer
    authentication_classes = (GovAuthentication,)

    def get_queryset(self, ids):
        return (
            GoodOnApplication.objects.filter(
                application_id=self.kwargs["case_pk"],
                id__in=ids,
            )
            .select_related("application", "good")
            .prefetch_related(
                "good__control_list_entries",
                "control_list_entries",
                "regime_entries",
            )
        )

    def get_application_line_numbers(self, instances):
        # Application line numbers are indexed in the order of the default application.goods
        # queryset.  Line numbers should start at 1
        line_numbers = {}
        application = StandardApplication.objects.get(id=self.kwargs["case_pk"])
        good_on_application_ids = [g.id for g in application.goods.all()]

        for item in instances:
            line_numbers[item.id] = good_on_application_ids.index(item.id) + 1

        return line_numbers

    def populate_report_summaries(self, assessment_data):
        # TODO: Remove this method once FE is updated

        payload = []

        for line_item in assessment_data:
            report_summaries = line_item.get("report_summaries", [])

            if is_legacy_line_item(data=line_item):
                payload.append({**line_item})
                continue

            if line_item["is_good_controlled"] is True:
                if not report_summaries:
                    report_summaries = [
                        {
                            "prefix": line_item["report_summary_prefix"],
                            "subject": line_item["report_summary_subject"],
                        },
                    ]

            payload.append({**line_item, "report_summaries": report_summaries})

        return payload

    def perform_update(self, serializer, user, line_numbers):
        serializer.save(user=user, line_numbers=line_numbers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        data = self.populate_report_summaries(request.data.copy())
        ids = validate_ids(data)
        instances = self.get_queryset(ids)
        line_numbers = self.get_application_line_numbers(instances)
        serializer = self.get_serializer(instances, data=data, partial=False, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer, user=request.user.govuser, line_numbers=line_numbers)

        return JsonResponse(data={}, status=status.HTTP_200_OK)


def validate_ids(data):

    ids = [record["id"] for record in data]
    duplicate_ids = [goa_id for goa_id, count in Counter(ids).items() if count > 1]

    if duplicate_ids:
        raise serializers.ValidationError(
            f"Multiple updates to a single GoodOnApplication id found. Duplicated ids; {','.join(duplicate_ids)}"
        )

    return ids
