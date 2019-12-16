import uuid

import reversion
from django.db import models
from model_utils.models import TimeStampedModel

from documents.models import Document
from flags.models import Flag
from goods.enums import GoodStatus, GoodControlled
from organisations.models import Organisation
from users.models import ExporterUser


@reversion.register()
class Good(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(max_length=280)
    is_good_controlled = models.CharField(choices=GoodControlled.choices, default=GoodControlled.UNSURE, max_length=20)
    control_code = models.TextField(default="", blank=True, null=True)
    is_good_end_product = models.BooleanField()
    part_number = models.TextField(default="", blank=True, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    status = models.CharField(choices=GoodStatus.choices, default=GoodStatus.DRAFT, max_length=20)
    flags = models.ManyToManyField(Flag, related_name="goods")

    # Gov
    comment = models.TextField(default=None, blank=True, null=True)
    report_summary = models.TextField(default=None, blank=True, null=True)


class GoodDocument(Document):
    good = models.ForeignKey(Good, on_delete=models.CASCADE)
    user = models.ForeignKey(ExporterUser, on_delete=models.DO_NOTHING)
    organisation = models.ForeignKey(Organisation, on_delete=models.DO_NOTHING)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
