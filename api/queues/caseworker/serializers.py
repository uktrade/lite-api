from rest_framework import serializers

from api.applications.serializers.advice import BulkApprovalAdviceSerializer
from api.cases.enums import AdviceLevel, AdviceType
from api.cases.models import Case
from api.core.serializers import PrimaryKeyRelatedField
from api.teams.models import Team


class BulkApprovalAdviceDataSerializer(serializers.Serializer):
    text = serializers.CharField()
    proviso = serializers.CharField(allow_blank=True, allow_null=True)
    note = serializers.CharField(allow_blank=True, allow_null=True)
    footnote_required = serializers.BooleanField(allow_null=True)
    footnote = serializers.CharField(allow_blank=True, allow_null=True)
    team = PrimaryKeyRelatedField(queryset=Team.objects.filter(is_ogd=True))


class BulkApprovalSerializer(serializers.Serializer):
    cases = PrimaryKeyRelatedField(many=True, queryset=Case.objects.all())
    advice = BulkApprovalAdviceDataSerializer()

    def get_advice_data(self, application, advice_fields):
        user = self.context["user"]
        subjects = [("good", good_on_application.good.id) for good_on_application in application.goods.all()] + [
            (poa.party.type, poa.party.id) for poa in application.parties.all()
        ]
        proviso = advice_fields.get("proviso", "")
        advice_type = AdviceType.PROVISO if proviso else AdviceType.APPROVE
        return [
            {
                "level": AdviceLevel.USER,
                "type": advice_type,
                "case": str(application.id),
                "user": user.govuser,
                subject_name: str(subject_id),
                "denial_reasons": [],
                **advice_fields,
            }
            for subject_name, subject_id in subjects
        ]

    def build_instances_data(self, validated_data):
        data = validated_data.copy()
        cases = data.get("cases", [])
        advice_fields = data.get("advice", {})
        instances_data = []
        for case in cases:
            advice_data = self.get_advice_data(case.baseapplication, advice_fields)
            instances_data.extend(advice_data)

        return instances_data

    def create(self, validated_data):
        data = self.build_instances_data(validated_data)
        advice_serializer = BulkApprovalAdviceSerializer(data=data, many=True)
        advice_serializer.is_valid(raise_exception=True)
        instances = advice_serializer.save()

        return instances
