from django.db import transaction
from django.http import JsonResponse
from rest_framework import generics, serializers
from rest_framework import status

from api.applications.models import GoodOnApplication, StandardApplication
from api.assessments.serializers import AssessmentSerializer
from api.core.authentication import GovAuthentication


class MakeAssessmentsView(generics.UpdateAPIView):

    serializer_class = AssessmentSerializer
    authentication_classes = (GovAuthentication,)

    def get_queryset(self, ids):
        return GoodOnApplication.objects.filter(
            application_id=self.kwargs["case_pk"],
            id__in=ids,
        )

    def get_application_line_numbers(self, instances):
        line_numbers = {}
        application = StandardApplication.objects.get(id=self.kwargs["case_pk"])
        good_on_application_ids = [g.id for g in application.goods.all()]

        for item in instances:
            line_numbers[item.id] = good_on_application_ids.index(item.id) + 1

        return line_numbers

    def perform_update(self, serializer, user, line_numbers):
        serializer.save(user=user, line_numbers=line_numbers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        ids = validate_ids(request.data)
        instances = self.get_queryset(ids)
        line_numbers = self.get_application_line_numbers(instances)
        serializer = self.get_serializer(instances, data=request.data, partial=False, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer, user=request.user.govuser, line_numbers=line_numbers)

        return JsonResponse(data={}, status=status.HTTP_200_OK)


def validate_ids(data, unique=True):

    ids = [record["id"] for record in data]

    if unique and len(ids) != len(set(ids)):
        raise serializers.ValidationError("Multiple updates to a single GoodOnApplication id found")

    return ids
