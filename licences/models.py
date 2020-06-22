import uuid

from django.db import models
from django.db.models import CheckConstraint, Q

from applications.models import BaseApplication, GoodOnApplication
from common.models import TimestampableModel
from licences.enums import LicenceStatus
from static.decisions.models import Decision


class Licence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        BaseApplication, on_delete=models.CASCADE, null=False, blank=False, related_name="licence"
    )
    status = models.CharField(max_length=32, default=LicenceStatus.DRAFT)
    start_date = models.DateField(blank=False, null=False)
    duration = models.PositiveSmallIntegerField(blank=False, null=False)
    decisions = models.ManyToManyField(Decision, related_name="licence")

    class Meta:
        constraints = [CheckConstraint(check=Q(status__in=LicenceStatus.values()), name='status_choices')]
        ordering = ("created_at",)

    def surrender(self):
        self.status = LicenceStatus.SURRENDERED
        self.save()

    def revoke(self):
        self.status = LicenceStatus.REVOKED
        self.save()


class GoodOnLicence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    good = models.ForeignKey(GoodOnApplication, on_delete=models.CASCADE)
    licence = models.ForeignKey(Licence, on_delete=models.CASCADE, related_name="goods", related_query_name="goods")
    usage = models.FloatField(null=False, blank=False, default=0)
    quantity = models.FloatField(null=True, blank=True, default=None)
    value = models.DecimalField(max_digits=256, decimal_places=2, null=True, blank=True, default=None)
