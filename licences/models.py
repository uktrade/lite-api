import uuid

from django.db import models

from applications.models import BaseApplication, GoodOnApplication
from common.models import TimestampableModel
from conf.settings import LITE_HMRC_INTEGRATION_ENABLED
from licences.enums import LicenceStatus
from licences.managers import LicenceManager
from static.decisions.models import Decision


class HMRCIntegrationUsageUpdate(TimestampableModel):
    """
    A history of when a Licence was updated via a Usage Update from HMRC Integration
    This is to prevent the same update from being processed multiple times
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Licence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(max_length=30, unique=True, editable=False)
    application = models.ForeignKey(
        BaseApplication, on_delete=models.CASCADE, null=False, blank=False, related_name="licences"
    )
    status = models.CharField(choices=LicenceStatus.choices, max_length=32, default=LicenceStatus.DRAFT)
    start_date = models.DateField(blank=False, null=False)
    duration = models.PositiveSmallIntegerField(blank=False, null=False)
    decisions = models.ManyToManyField(Decision, related_name="licence")
    hmrc_integration_sent_at = models.DateTimeField(blank=True, null=True)  # When licence was sent to HMRC Integration
    hmrc_integration_usage_updates = models.ManyToManyField(
        HMRCIntegrationUsageUpdate, related_name="licences"
    )  # Usage Update IDs from from HMRC Integration

    objects = LicenceManager()

    def surrender(self):
        self.status = LicenceStatus.SURRENDERED
        self.save()

    def cancel(self, is_being_re_issued=False):
        self.status = LicenceStatus.CANCELLED

        if is_being_re_issued:
            # For avoiding use of 'save()' which would trigger 'send_to_hmrc_integration()' again
            # If the licence is being re-issued, we want to send the re-issue licence
            super(Licence, self).save()
        else:
            self.save()

    def issue(self):
        # re-issue the licence if an older version exists
        try:
            old_licence = Licence.objects.get(
                application=self.application, status__in=[LicenceStatus.ISSUED, LicenceStatus.REINSTATED]
            )
            old_licence.cancel(is_being_re_issued=True)
        except Licence.DoesNotExist:
            old_licence = None

        self.status = LicenceStatus.ISSUED if not old_licence else LicenceStatus.REINSTATED
        self.save()

    def save(self, *args, **kwargs):
        super(Licence, self).save(*args, **kwargs)

        if LITE_HMRC_INTEGRATION_ENABLED and self.status != LicenceStatus.DRAFT:
            self.send_to_hmrc_integration()

    def send_to_hmrc_integration(self):
        from licences.tasks import schedule_licence_for_hmrc_integration

        schedule_licence_for_hmrc_integration(str(self.id), LicenceStatus.hmrc_intergration_action.get(self.status))

    def set_hmrc_integration_sent_at(self, value):
        """
        For avoiding use of 'save()' which would trigger 'send_to_hmrc_integration()' again
        """
        self.hmrc_integration_sent_at = value
        super(Licence, self).save()


class GoodOnLicence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    good = models.ForeignKey(GoodOnApplication, on_delete=models.CASCADE, related_name="licence")
    licence = models.ForeignKey(Licence, on_delete=models.CASCADE, related_name="goods", related_query_name="goods")
    usage = models.FloatField(null=False, blank=False, default=0)
    quantity = models.FloatField(null=False, blank=False)
    value = models.DecimalField(max_digits=15, decimal_places=2, null=False, blank=False)
