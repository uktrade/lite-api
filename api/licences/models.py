import uuid
from datetime import datetime
from api.audit_trail.enums import AuditType
import reversion

from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from api.applications.models import GoodOnApplication
from api.cases.enums import LicenceDecisionType
from api.cases.models import Case, LicenceDecision
from api.common.models import TimestampableModel
from api.core.helpers import add_months
from api.licences.enums import LicenceStatus, licence_status_to_hmrc_integration_action
from api.licences.managers import LicenceManager
from api.staticdata.decisions.models import Decision
from api.cases.notify import notify_exporter_licence_suspended, notify_exporter_licence_revoked
from api.audit_trail import service as audit_trail_service


class HMRCIntegrationUsageData(TimestampableModel):
    """
    A history of when a Licence was updated via a Usage Update from HMRC Integration
    This is to prevent the same update from being processed multiple times
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


@reversion.register()
class Licence(TimestampableModel):
    """
    A licence issued to an exporter application
    """

    DATETIME_FORMAT = "%Y-%m-%d"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(max_length=30, unique=True, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, null=False, blank=False, related_name="licences")
    status = models.CharField(choices=LicenceStatus.choices, max_length=32, default=LicenceStatus.DRAFT)
    start_date = models.DateField(blank=False, null=False)
    end_date = models.DateField(blank=False, null=False)
    duration = models.PositiveSmallIntegerField(blank=False, null=False)
    decisions = models.ManyToManyField(Decision, related_name="licence")
    hmrc_integration_sent_at = models.DateTimeField(blank=True, null=True)  # When licence was sent to HMRC Integration
    hmrc_integration_usage_updates = models.ManyToManyField(
        HMRCIntegrationUsageData, related_name="licences"
    )  # Usage Update IDs from from HMRC Integration

    objects = LicenceManager()

    def __str__(self):
        return self.reference_code

    def _set_status(self, status, user=None, send_status_change_to_hmrc=True):
        original_status = self.status
        self.status = status
        self.save(send_status_change_to_hmrc=send_status_change_to_hmrc)
        status_changed = original_status != self.status
        if status_changed:
            self.create_licence_change_audit_log(original_status=original_status, user=user)

    def hmrc_mail_status(self):
        """
        Fetch mail status from HRMC-integration server
        """
        from api.licences.libraries.hmrc_integration_operations import get_mail_status

        if not settings.LITE_HMRC_INTEGRATION_ENABLED:
            raise ImproperlyConfigured("Did you forget to switch on LITE_HMRC_INTEGRATION_ENABLED?")
        return get_mail_status(self)

    def create_licence_change_audit_log(self, original_status=None, user=None):
        """
        Generates a system audit log for licence changes
        """
        audit_kwargs = {
            "verb": AuditType.LICENCE_UPDATED_STATUS,
            "action_object": self,
            "target": self.case.get_case(),
            "payload": {"licence": self.reference_code, "status": self.status, "previous_status": original_status},
        }
        if user:
            audit_trail_service.create(
                **audit_kwargs,
                actor=user,
            )
        else:
            audit_trail_service.create_system_user_audit(**audit_kwargs)

    def surrender(self, user=None):
        self._set_status(status=LicenceStatus.SURRENDERED, user=user, send_status_change_to_hmrc=True)

    def suspend(self, user=None):
        self._set_status(LicenceStatus.SUSPENDED, user, send_status_change_to_hmrc=False)
        notify_exporter_licence_suspended(self)

    def revoke(self, user=None):
        self._set_status(LicenceStatus.REVOKED, user=user, send_status_change_to_hmrc=True)
        LicenceDecision.objects.create(
            case=self.case,
            decision=LicenceDecisionType.REVOKED,
            licence=self,
        )
        notify_exporter_licence_revoked(self)

    def cancel(self, user=None, send_status_change_to_hmrc=True):
        self._set_status(
            status=LicenceStatus.CANCELLED, user=user, send_status_change_to_hmrc=send_status_change_to_hmrc
        )

    def reinstate(self, user=None):
        # This supersedes the issue method as it's called explicity on the licence
        # Hence the user explicty knows which license is being reinstated
        self._set_status(status=LicenceStatus.REINSTATED, user=user, send_status_change_to_hmrc=True)

    def issue(self, user=None, send_status_change_to_hmrc=True):
        # re-issue the licence if an older version exists
        status = LicenceStatus.ISSUED
        old_licence = (
            Licence.objects.filter(case=self.case).exclude(status=LicenceStatus.DRAFT).order_by("-created_at").first()
        )
        if old_licence:
            old_licence.cancel(send_status_change_to_hmrc=False)
            status = LicenceStatus.REINSTATED

        self._set_status(status=status, user=user, send_status_change_to_hmrc=send_status_change_to_hmrc)

    def save(self, *args, **kwargs):
        end_datetime = datetime.strptime(
            add_months(self.start_date, self.duration, self.DATETIME_FORMAT), self.DATETIME_FORMAT
        )
        self.end_date = end_datetime.date()

        send_status_change_to_hmrc = kwargs.pop("send_status_change_to_hmrc", False)

        # We only require a system log if this is a new save since this isn't user initiated

        if not Licence.objects.filter(id=self.id).exists():
            self.create_licence_change_audit_log()
        super(Licence, self).save(*args, **kwargs)

        # Immediately notify HMRC if needed
        if settings.LITE_HMRC_INTEGRATION_ENABLED and send_status_change_to_hmrc and self.status != LicenceStatus.DRAFT:
            self.send_to_hmrc_integration()

    def send_to_hmrc_integration(self):
        from api.licences.celery_tasks import schedule_licence_details_to_lite_hmrc

        schedule_licence_details_to_lite_hmrc(str(self.id), licence_status_to_hmrc_integration_action.get(self.status))


class GoodOnLicence(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    good = models.ForeignKey(GoodOnApplication, on_delete=models.CASCADE, related_name="licence")
    licence = models.ForeignKey(Licence, on_delete=models.CASCADE, related_name="goods", related_query_name="goods")
    usage = models.FloatField(null=False, blank=False, default=0)
    quantity = models.FloatField(null=False, blank=False)
    value = models.DecimalField(max_digits=15, decimal_places=2, null=False, blank=False)

    class Meta:
        unique_together = ("licence", "good")
        indexes = [
            models.Index(fields=["created_at"]),
        ]
