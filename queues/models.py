import uuid

from django.db import models
from django.db.models.functions import Coalesce

from teams.models import Team


class Queue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(default="Untitled Queue")
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    class Meta:
        ordering = ["name"]

    def get_cases(self):
        from cases.models import Case

        if hasattr(self, "query"):
            ordering = (
                "-created_at" if hasattr(self, "reverse_ordering") else "created_at"
            )
            cases = (
                Case.objects.annotate(
                    created_at=Coalesce(
                        "application__submitted_at", "query__submitted_at"
                    ),
                    status__priority=Coalesce(
                        "application__status__priority", "query__status__priority"
                    ),
                )
                .filter(self.query)
                .order_by(ordering)
            )

            return cases
        else:
            return self.cases
