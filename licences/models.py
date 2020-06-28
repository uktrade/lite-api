import uuid

from django.db import models
from django.db.models import CheckConstraint, Q

from applications.models import BaseApplication, GoodOnApplication
from common.models import TimestampableModel
from conf.settings import LITE_HMRC_INTEGRATION_ENABLED
from licences.enums import LicenceStatus
from licences.managers import LicenceManager
from static.decisions.models import Decision


class Licence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(max_length=30, unique=True, editable=False)
    application = models.ForeignKey(
        BaseApplication, on_delete=models.CASCADE, null=False, blank=False, related_name="licence"
    )
    status = models.CharField(
        choices=[(tag.value, tag) for tag in LicenceStatus], max_length=32, default=LicenceStatus.DRAFT.value
    )
    start_date = models.DateField(blank=False, null=True)
    duration = models.PositiveSmallIntegerField(blank=False, null=True)
    decisions = models.ManyToManyField(Decision, related_name="licence")
    sent_at = models.DateTimeField(blank=True, null=True)  # When licence was sent to HMRC Integration

    objects = LicenceManager()

    class Meta:
        constraints = [CheckConstraint(check=Q(status__in=LicenceStatus.values()), name="status_choices")]
        ordering = ("created_at",)

    def surrender(self):
        self.status = LicenceStatus.SURRENDERED.value
        self.save()

    def revoke(self):
        self.status = LicenceStatus.REVOKED.value
        self.save()

    def cancel(self):
        self.status = LicenceStatus.CANCELLED.value
        self.save()

    def issue(self):
        try:
            old_licence = Licence.objects.get(application=self.application, status=LicenceStatus.ISSUED.value)
            old_licence.cancel()
        except Licence.DoesNotExist:
            old_licence = None

        self.status = LicenceStatus.ISSUED.value if not old_licence else LicenceStatus.REINSTATED.value
        self.save()

    def is_complete(self):
        return self.status in [LicenceStatus.ISSUED.value, LicenceStatus.REINSTATED.value]

    def save(self, *args, **kwargs):
        super(Licence, self).save(*args, **kwargs)

        if LITE_HMRC_INTEGRATION_ENABLED and self.is_complete():
            self.send_to_hmrc_integration()

    def send_to_hmrc_integration(self):
        from licences.tasks import schedule_licence_for_hmrc_integration

        schedule_licence_for_hmrc_integration(str(self.id), self.reference_code)

    def set_sent_at(self, value):
        """
        For avoiding use of 'save()' which would trigger 'send_to_hmrc_integration()' again
        """

        self.sent_at = value
        super(Licence, self).save()


class GoodOnLicence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    good = models.ForeignKey(GoodOnApplication, on_delete=models.CASCADE, related_name="licence")
    licence = models.ForeignKey(Licence, on_delete=models.CASCADE, related_name="goods", related_query_name="goods")
    usage = models.FloatField(null=False, blank=False, default=0)
    quantity = models.FloatField(null=True, blank=True, default=None)
    value = models.DecimalField(max_digits=256, decimal_places=2, null=True, blank=True, default=None)
