from rest_framework.relations import PrimaryKeyRelatedField

from conf.serializers import PrimaryKeyRelatedSerializerField


class CaseAssignmentRelatedSerializerField(PrimaryKeyRelatedSerializerField):
    """
    Custom field serializer required for optional query filtering based on current queue
    """
    def __init__(self, **kwargs):
        from cases.serializers import QueueCaseAssignmentSerializer

        self.serializer = QueueCaseAssignmentSerializer
        self.many = True

        super(PrimaryKeyRelatedSerializerField, self).__init__(**kwargs)

    def get_queryset(self):
        queryset = super(CaseAssignmentRelatedSerializerField, self).get_queryset()
        queue = self.context["queue_id"] if not self.context["is_system_queue"] else None

        if queue:
            return queryset.filter(queue=queue)
        else:
            return queryset.all()


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
            return (
                queryset.select_related("raised_by_user__team_id")
                .filter(raised_by_user__team_id=team, responded_at__isnull=True)
            )

    def to_representation(self, value):
        return value.exists()
