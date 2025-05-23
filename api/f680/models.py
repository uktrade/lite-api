from django.utils import timezone
import uuid

from dateutil.relativedelta import relativedelta


from django.db import models
from django.contrib.postgres.fields import ArrayField
from copy import deepcopy

from api.applications.models import BaseApplication
from api.cases.celery_tasks import get_application_target_sla
from api.cases.models import Case
from api.common.models import TimestampableModel
from api.organisations.models import Organisation
from api.staticdata.countries.models import Country
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.teams.models import Team
from api.users.models import GovUser
from api.cases.enums import AdviceType
from api.audit_trail.enums import AuditType
from api.audit_trail import service as audit_trail_service

from api.f680.managers import F680ApplicationQuerySet
from api.f680 import enums
from api.f680.utils import get_application_answer
from api.core.model_mixins import Clonable
from api.staticdata.statuses.enums import CaseStatusEnum, CaseStatusIdEnum, CaseSubStatusIdEnum


class SecurityGradingMixin:
    @property
    def security_grading_final(self):
        composed_security_grading_prefix = (
            self.composed_security_grading_prefix.upper() if self.composed_security_grading_prefix else ""
        )
        composed_security_grading = self.composed_security_grading.upper() if self.composed_security_grading else ""

        return f"{composed_security_grading_prefix} {composed_security_grading}" if composed_security_grading else None

    @property
    def composed_security_grading_prefix(self):
        return (
            self.security_grading_prefix_other
            if self.security_grading_prefix == enums.SecurityGradingPrefix.OTHER
            else self.get_security_grading_prefix_display()
        )

    @property
    def composed_security_grading(self):
        return (
            self.security_grading_other
            if self.security_grading == enums.SecurityGrading.OTHER
            else self.get_security_grading_display()
        )


class F680Application(BaseApplication, Clonable):
    objects = F680ApplicationQuerySet.as_manager()
    application = models.JSONField()

    clone_exclusions = [
        "appeal",
        "appeal_deadline",
        "id",
        "flags",
        "queues",
        "reference_code",
        "submitted_at",
        "submitted_by",
        "status",
        "sub_status",
        "case_officer",
        "copy_of",
        "amendment_of",
        "sla_days",
        "sla_remaining_days",
        "sla_updated_at",
        "additional_contacts",
        "case_ptr",
        "baseapplication_ptr",
        "last_closed_at",
        "foi_reason",
        "agreed_to_foi",
    ]
    clone_mappings = {
        "organisation": "organisation_id",
        "case_type": "case_type_id",
    }
    clone_overrides = {
        "status_id": CaseStatusIdEnum.DRAFT,
    }

    def clone(self, exclusions=None, **overrides):
        cloned_application = super().clone(exclusions=exclusions, **overrides)
        application_data = deepcopy(cloned_application.application)
        try:
            items = application_data["sections"]["user_information"]["items"]
        except KeyError:
            return cloned_application

        for item in items:
            item["id"] = str(uuid.uuid4())

        application_data["sections"]["user_information"]["items"] = items
        cloned_application.application = application_data
        cloned_application.save()
        return cloned_application

    def get_product(self):
        if self.security_release_requests.count() == 0:
            return None
        return self.security_release_requests.first().product

    def on_submit(self, application_data):

        previous_status = self.status.status

        self.name = application_data["sections"]["general_application_details"]["fields"]["name"]["raw_answer"]
        self.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        self.submitted_at = timezone.now()
        self.sla_remaining_days = get_application_target_sla(self.case_type.sub_type)
        self.sla_days = 0

        self.save()
        self.audit_on_submit(previous_status)

        product_information_fields = application_data["sections"]["product_information"]["fields"]
        # Create the Product for this application - F680s just have the one

        product = Product.objects.create(
            name=application_data["sections"]["product_information"]["fields"]["product_name"]["raw_answer"],
            description=application_data["sections"]["product_information"]["fields"]["product_description"][
                "raw_answer"
            ],
            organisation=self.organisation,
            security_grading_prefix=get_application_answer(product_information_fields, "prefix"),
            security_grading_prefix_other=get_application_answer(product_information_fields, "other_prefix"),
            security_grading=get_application_answer(product_information_fields, "security_classification"),
            security_grading_other=get_application_answer(product_information_fields, "other_security_classification"),
        )

        # Create a Recipient and SecurityRelease for each.  In F680s caseworkers
        #   will advise against SecurityRelease records
        for item in application_data["sections"]["user_information"]["items"]:
            item_fields = item["fields"]

            recipient = Recipient.objects.create(
                name=item_fields["end_user_name"]["raw_answer"],
                address=item_fields["address"]["raw_answer"],
                country_id=item_fields["country"]["raw_answer"],
                type=item_fields["entity_type"]["raw_answer"],
                organisation=self.organisation,
                role=item_fields["third_party_role"]["raw_answer"] if "third_party_role" in item_fields else None,
                role_other=(
                    item_fields["third_party_role_other"]["raw_answer"]
                    if "third_party_role_other" in item_fields
                    else None
                ),
            )

            SecurityReleaseRequest.objects.create(
                id=item["id"],  # Use the JSON item ID for the security release so we can tally the two easily later
                recipient=recipient,
                product=product,
                application=self,
                security_grading_prefix=item_fields["prefix"]["raw_answer"],
                security_grading=item_fields["security_classification"]["raw_answer"],
                intended_use=item_fields["end_user_intended_end_use"]["raw_answer"],
                security_grading_prefix_other=get_application_answer(item_fields, "other_prefix"),
                security_grading_other=get_application_answer(item_fields, "other_security_classification"),
                approval_types=application_data["sections"]["approval_type"]["fields"]["approval_choices"][
                    "raw_answer"
                ],
            )

    def get_required_decision_document_types(self):
        all_outcomes = set(
            SecurityReleaseOutcome.objects.filter(case=self.case_ptr)
            .order_by("outcome")
            .distinct("outcome")
            .values_list("outcome", flat=True)
        )

        return all_outcomes

    @classmethod
    def get_decision_actions(cls):
        return {
            AdviceType.APPROVE: cls.approve,
            AdviceType.REFUSE: cls.refuse,
        }

    def approve(self):
        self.set_sub_status(CaseSubStatusIdEnum.FINALISED__APPROVED)

    def refuse(self):
        self.set_sub_status(CaseSubStatusIdEnum.FINALISED__REFUSED)

    def finalise_decisions(self, user):
        from api.cases.notify import notify_exporter_f680_outcome_issued

        notify_exporter_f680_outcome_issued(self)
        audit_trail_service.create(
            actor=user,
            verb=AuditType.FINALISED_APPLICATION,
            target=self,
            payload={
                "case_reference": self.reference_code,
            },
        )

    def manage_decisions(self, user, decisions, **kwargs):
        decision_actions = self.get_decision_actions()
        ordered_decisions = sorted(decisions, reverse=True)
        for advice_type in ordered_decisions:
            decision_actions[advice_type](self)
        self.finalise_decisions(user)


# TODO: Eventually we may want to use this model more widely.  We can do that
#   but for now baking it in to the f680 application avoids us having to guess
#   at unknown futures
class Recipient(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    address = models.TextField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    type = models.CharField(choices=enums.RecipientType.choices, max_length=50)
    role = models.CharField(choices=enums.RecipientRole.choices, max_length=50, default=None, null=True)
    role_other = models.TextField(null=True, default=None)
    organisation = models.ForeignKey(Organisation, related_name="organisation_recipient", on_delete=models.CASCADE)


# TODO: Eventually we may want to use this model more widely.  We can do that
#   but for now baking it in to the f680 application avoids us having to guess
#   at unknown futures
class Product(TimestampableModel, SecurityGradingMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField()
    security_grading_prefix = models.CharField(
        choices=enums.SecurityGradingPrefix.prefix_choices, max_length=50, null=True, default=None
    )
    security_grading_prefix_other = models.TextField(null=True, default=None)
    security_grading = models.CharField(
        choices=enums.SecurityGrading.product_choices, max_length=50, null=True, default=None
    )
    security_grading_other = models.TextField(null=True, default=None)
    organisation = models.ForeignKey(Organisation, related_name="organisation_product", on_delete=models.CASCADE)


class SecurityReleaseRequest(TimestampableModel, SecurityGradingMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, related_name="security_release_requests")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="security_release_requests")
    application = models.ForeignKey(F680Application, on_delete=models.CASCADE, related_name="security_release_requests")
    security_grading_prefix = models.CharField(
        choices=enums.SecurityGradingPrefix.prefix_choices, max_length=50, null=True, default=None
    )
    security_grading_prefix_other = models.TextField(null=True, default=None)
    security_grading = models.CharField(choices=enums.SecurityGrading.security_release_choices, max_length=50)
    security_grading_other = models.TextField(null=True, default=None)
    approval_types = ArrayField(models.CharField(choices=enums.ApprovalTypes.choices, max_length=50))
    # We need details of the release, this doesn't appear to be in the frontend flows yet..
    intended_use = models.TextField()


class Recommendation(TimestampableModel, SecurityGradingMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, related_name="recommendations", on_delete=models.CASCADE)
    type = models.CharField(choices=enums.RecommendationType.choices, max_length=30)
    security_grading_prefix = models.CharField(
        choices=enums.SecurityGradingPrefix.prefix_choices, max_length=50, null=True, default=None
    )
    security_grading_prefix_other = models.TextField(default="", blank=True, null=True)
    security_grading = models.CharField(
        choices=enums.SecurityGrading.security_release_choices, blank=True, null=True, max_length=50
    )
    security_grading_other = models.TextField(default="", blank=True, null=True)
    conditions = models.TextField(default="", blank=True, null=True)
    refusal_reasons = models.TextField(default="", blank=True, null=True)
    user = models.ForeignKey(GovUser, on_delete=models.PROTECT, related_name="recommendations")
    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="recommendations", null=True)
    security_release_request = models.ForeignKey(
        SecurityReleaseRequest, related_name="recommendations", on_delete=models.CASCADE
    )


class SecurityReleaseOutcome(TimestampableModel, SecurityGradingMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, related_name="security_release_outcomes", on_delete=models.CASCADE)
    security_release_requests = models.ManyToManyField(SecurityReleaseRequest)
    user = models.ForeignKey(GovUser, on_delete=models.PROTECT, related_name="security_release_outcomes")
    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="security_release_outcomes", null=True)
    outcome = models.CharField(choices=enums.SecurityReleaseOutcomes.choices, max_length=30)
    conditions = models.TextField(default="", blank=True, null=True)
    refusal_reasons = models.TextField(default="", blank=True, null=True)
    security_grading_prefix = models.CharField(
        choices=enums.SecurityGradingPrefix.prefix_choices, blank=True, null=True, max_length=50
    )
    security_grading_prefix_other = models.TextField(default="", blank=True, null=True)
    security_grading = models.CharField(
        choices=enums.SecurityGrading.security_release_outcome_choices, max_length=50, blank=True, null=True
    )
    security_grading_other = models.TextField(default="", blank=True, null=True)
    approval_types = ArrayField(models.CharField(choices=enums.ApprovalTypes.choices, max_length=50), default=list)
    validity_start_date = models.DateField(blank=True, null=True, help_text="Date the outcome validity starts")
    validity_end_date = models.DateField(blank=True, null=True, help_text="Date the outcome is no longer valid")

    @property
    def validity_period(self) -> int:
        """Returns outcome validity period in months"""
        duration = 0
        if (
            self.outcome == enums.SecurityReleaseOutcomes.APPROVE
            and self.validity_start_date
            and self.validity_end_date
        ):
            diff = relativedelta(self.validity_end_date, self.validity_start_date)
            duration = diff.years * 12 + diff.months

        return duration
