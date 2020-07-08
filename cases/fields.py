from rest_framework.relations import PrimaryKeyRelatedField


class HasOpenECJUQueriesRelatedField(PrimaryKeyRelatedField):
    """
    Custom field serializer required to determine if a case has open ECJU queries
    """

    def use_pk_only_optimization(self):
        return False

    def get_queryset(self):
        queryset = super().get_queryset()
        include_hidden = self.context["include_hidden"]
        team = self.context["team"]
        if include_hidden:
            return queryset.select_related("raised_by_user__team_id").filter(
                raised_by_user__team_id=team, responded_at__isnull=True
            )

    def to_representation(self, value):
        return value.exists()
