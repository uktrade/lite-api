from django_filters import rest_framework as filters

from api.cases.enums import AdviceType
from api.letter_templates.models import LetterTemplate


class LetterTemplateFilter(filters.FilterSet):
    case_type = filters.CharFilter(field_name="case_types__sub_type", lookup_expr="exact")
    decision = filters.MultipleChoiceFilter(
        field_name="decisions__name", choices=AdviceType.choices, lookup_expr="exact"
    )

    class Meta:
        model = LetterTemplate
        fields = (
            "case_types",
            "decisions",
        )
