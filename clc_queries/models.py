import uuid
import reversion
from django.db import models
from clc_queries.enums import ClcQueryStatus
from goods.models import Good


@reversion.register()
class ClcQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    details = models.TextField(default=None, blank=True, null=True)
    good = models.ForeignKey(Good, on_delete=models.DO_NOTHING, null=False)
    status = models.CharField(choices=ClcQueryStatus.choices, default=ClcQueryStatus.SUBMITTED, max_length=50)
