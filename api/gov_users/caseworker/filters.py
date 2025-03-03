from django_filters import rest_framework as filters

from api.users.models import GovUser


class GovUserFilter(filters.FilterSet):
    email = filters.CharFilter(field_name="baseuser_ptr__email", lookup_expr="exact")

    class Meta:
        model = GovUser
        fields = ("email",)
