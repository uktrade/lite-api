import uuid

from django.db import models

from applications.models import BaseApplication, GoodOnApplication
from common.models import TimestampableModel
from conf.settings import LITE_HMRC_INTEGRATION_ENABLED
from static.decisions.models import Decision


class Licence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(max_length=30, unique=True, editable=False)
    application = models.ForeignKey(
        BaseApplication, on_delete=models.CASCADE, null=False, blank=False, related_name="licence"
    )
    start_date = models.DateField(blank=False, null=False)
    duration = models.PositiveSmallIntegerField(blank=False, null=False)
    is_complete = models.BooleanField(default=False, null=False, blank=False)
    decisions = models.ManyToManyField(Decision, related_name="licence")
    sent_at = models.DateTimeField(blank=True, null=True)  # When licence was sent to HMRC Integration

    def save(self, *args, **kwargs):
        super(Licence, self).save(*args, **kwargs)

        if LITE_HMRC_INTEGRATION_ENABLED and self.is_complete:
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


class LicenceUsageUpdateTransaction(TimestampableModel):
    """
    A history of when Licence Good Usages were updated via HMRC Integration
    This is to prevent the same Usage update from being processed multiple times
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    licences = models.ManyToManyField(Licence, related_name="usage_update_transactions")
