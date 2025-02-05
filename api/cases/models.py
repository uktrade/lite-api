import logging
import uuid
from collections import defaultdict
from typing import Optional

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from api.users.enums import UserType

from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import queryable_property

from api.audit_trail.enums import AuditType
from api.cases.enums import (
    AdviceType,
    CaseDocumentState,
    CaseTypeTypeEnum,
    CaseTypeSubTypeEnum,
    CaseTypeReferenceEnum,
    ECJUQueryType,
    AdviceLevel,
    EnforcementXMLEntityTypes,
    LicenceDecisionType,
)
from api.cases.helpers import working_days_in_range
from api.cases.libraries.reference_code import generate_reference_code
from api.cases.managers import CaseManager, CaseReferenceCodeManager, AdviceManager
from api.common.models import TimestampableModel
from api.documents.models import Document
from api.flags.models import Flag
from api.goods.enums import PvGrading
from api.organisations.models import Organisation
from api.queues.models import Queue
from api.staticdata.decisions.models import Decision
from api.staticdata.denial_reasons.models import DenialReason
from api.staticdata.statuses.enums import CaseStatusEnum, CaseSubStatusIdEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.statuses.models import (
    CaseStatus,
    CaseSubStatus,
)
from api.teams.models import Team, Department
from api.users.models import (
    BaseUser,
    ExporterUser,
    GovUser,
    UserOrganisationRelationship,
    ExporterNotification,
)

denial_reasons_logger = logging.getLogger(settings.DENIAL_REASONS_DELETION_LOGGER)


class CaseTypeManager(models.Manager):
    def get_by_natural_key(self, reference):
        return self.get(reference=reference)


class CaseType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(choices=CaseTypeTypeEnum.choices, null=False, blank=False, max_length=35)
    sub_type = models.CharField(choices=CaseTypeSubTypeEnum.choices, null=False, blank=False, max_length=35)
    reference = models.CharField(
        choices=CaseTypeReferenceEnum.choices,
        unique=True,
        null=False,
        blank=False,
        max_length=6,
    )

    objects = CaseTypeManager()

    def natural_key(self):
        return (self.reference,)


class BadSubStatus(ValueError):
    pass


class Case(TimestampableModel):
    """
    Base model for applications and queries
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    reference_code = models.CharField(max_length=30, unique=True, null=True, blank=False, editable=False, default=None)
    case_type = models.ForeignKey(CaseType, on_delete=models.DO_NOTHING, null=False, blank=False)
    queues = models.ManyToManyField(Queue, related_name="cases", through="CaseQueue")
    flags = models.ManyToManyField(Flag, related_name="cases")
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="cases")
    submitted_at = models.DateTimeField(blank=True, null=True)
    submitted_by = models.ForeignKey(ExporterUser, null=True, on_delete=models.DO_NOTHING)
    status = models.ForeignKey(
        CaseStatus,
        related_name="query_status",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    sub_status = models.ForeignKey(
        CaseSubStatus,
        related_name="sub_status",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    case_officer = models.ForeignKey(GovUser, null=True, on_delete=models.DO_NOTHING)
    copy_of = models.ForeignKey("self", default=None, null=True, on_delete=models.DO_NOTHING)
    amendment_of = models.ForeignKey(
        "self", default=None, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="amendment"
    )
    last_closed_at = models.DateTimeField(null=True)

    sla_days = models.PositiveSmallIntegerField(null=False, blank=False, default=0)
    sla_remaining_days = models.SmallIntegerField(null=True)
    sla_updated_at = models.DateTimeField(null=True)
    additional_contacts = models.ManyToManyField("parties.Party", related_name="case")
    audit_trail = GenericRelation(
        "audit_trail.Audit",
        related_query_name="case",
        content_type_field="target_content_type",
        object_id_field="target_object_id",
    )
    # _previous_status is used during post_save signal to check if the status has changed
    _previous_status = None

    objects = CaseManager()

    def save(self, *args, **kwargs):
        if CaseStatusEnum.is_terminal(self.status.status):
            self.case_officer = None
            if self.pk:
                self.queues.clear()
            CaseAssignment.objects.filter(case=self).delete()

        if not self.reference_code and self.status != get_case_status_by_status(CaseStatusEnum.DRAFT):
            self.reference_code = generate_reference_code(self)

        self._reset_sub_status_on_status_change()

        super(Case, self).save(*args, **kwargs)

    @classmethod
    def get_decision_actions(cls):
        return {
            AdviceType.APPROVE: cls.approve,
            AdviceType.REFUSE: cls.refuse,
            AdviceType.NO_LICENCE_REQUIRED: cls.no_licence_required,
            AdviceType.INFORM: lambda x: x,
        }

    def _reset_sub_status_on_status_change(self):
        from api.audit_trail import service as audit_trail_service

        status_changed = False
        try:
            case = Case.objects.get(id=self.pk)
        except Case.DoesNotExist:
            return  # If our case record does not yet exist in the DB, return early
        old_status = case.status
        status_changed = old_status != self.status
        if status_changed and self.sub_status:
            self.sub_status = None
            audit_trail_service.create_system_user_audit(
                verb=AuditType.UPDATED_SUB_STATUS,
                target=case,
                payload={"sub_status": None, "status": CaseStatusEnum.get_text(self.status.status)},
            )

    @property
    def superseded_by(self):
        if not self.amendment.exists():
            return None
        return self.amendment.first()

    def get_case(self):
        """
        For any child models, this method allows easy access to the parent Case.

        Child cases [StandardApplication, ...] share `id` with Case.
        """
        if type(self) == Case:  # noqa
            return self

        return Case.objects.get(id=self.id)

    def get_assigned_users(self):
        case_assignments = self.case_assignments.select_related("queue", "user").order_by("queue__name")
        return_value = defaultdict(list)

        for assignment in case_assignments:
            return_value[assignment.queue.name].append(
                {
                    "id": assignment.user.pk,
                    "first_name": assignment.user.first_name,
                    "last_name": assignment.user.last_name,
                    "email": assignment.user.email,
                    "assignment_id": assignment.pk,
                }
            )

        return return_value

    def change_status(self, user, status: CaseStatus, note: Optional[str] = ""):
        """
        Sets the status for the case, runs validation on various parameters,
        creates audit entries and also runs flagging and automation rules
        """
        from api.applications.notify import notify_exporter_case_opened_for_editing
        from api.audit_trail import service as audit_trail_service
        from api.cases.libraries.finalise import remove_flags_on_finalisation, remove_flags_from_audit_trail
        from api.licences.helpers import update_licence_status
        from lite_routing.routing_rules_internal.routing_engine import run_routing_rules

        old_status = self.status.status

        self.status = status
        self.save()

        # Update licence status if applicable case status change
        update_licence_status(self, status.status)

        audit_trail_service.create(
            actor=user,
            verb=AuditType.UPDATED_STATUS,
            target=self.get_case(),
            payload={
                "status": {"new": self.status.status, "old": old_status},
                "additional_text": note,
            },
        )

        if old_status != self.status.status:
            run_routing_rules(case=self, keep_status=True)

            if status.status == CaseStatusEnum.APPLICANT_EDITING:
                notify_exporter_case_opened_for_editing(self)

        # Remove needed flags when case is Withdrawn/Closed
        if status.status in [CaseStatusEnum.WITHDRAWN, CaseStatusEnum.CLOSED]:
            remove_flags_on_finalisation(self)
            remove_flags_from_audit_trail(self)

    def parameter_set(self):
        """
        This function looks at the case determines the flags, casetype, and countries of that case,
            and puts these objects into a set
        :return: set object
        """
        from api.applications.models import PartyOnApplication
        from api.applications.models import GoodOnApplication

        parameter_set = set(self.flags.all()) | {self.case_type} | set(self.organisation.flags.all())

        for poa in PartyOnApplication.objects.filter(application=self.id, deleted_at__isnull=True):
            parameter_set = (
                parameter_set | {poa.party.country} | set(poa.party.flags.all()) | set(poa.party.country.flags.all())
            )

        for goa in GoodOnApplication.objects.filter(application=self.id):
            parameter_set = parameter_set | set(goa.good.flags.all())

        return parameter_set

    def remove_all_case_assignments(self):
        """
        Removes all queue and user assignments, and also audits the removal of said assignments against the case
        """
        from api.audit_trail import service as audit_trail_service

        case = self.get_case()
        assigned_cases = CaseAssignment.objects.filter(case=case)

        if self.queues.exists():
            self.queues.clear()

            audit_trail_service.create_system_user_audit(
                verb=AuditType.REMOVE_CASE_FROM_ALL_QUEUES,
                action_object=case,
            )

        if assigned_cases.exists():
            assigned_cases.delete()

            audit_trail_service.create_system_user_audit(
                verb=AuditType.REMOVE_CASE_FROM_ALL_USER_ASSIGNMENTS,
                action_object=case,
            )

    def get_case_officer_name(self):
        """
        Returns the name of the case officer
        """
        if self.case_officer:
            return self.case_officer.baseuser_ptr.get_full_name()

    def set_sub_status(self, sub_status_id):
        """
        Set the sub_status on this case.  Raises Exception if this sub_status
        is not a vaild child sub_status of the current case status.
        """
        from api.audit_trail import service as audit_trail_service

        sub_status = CaseSubStatus.objects.get(id=sub_status_id)
        if sub_status.parent_status != self.status:
            raise BadSubStatus(f"{sub_status.name} is not a child of {self.status.status}")
        self.sub_status = sub_status
        self.save()

        # Create an audit event for the sub status
        case = self.get_case()
        audit_trail_service.create_system_user_audit(
            verb=AuditType.UPDATED_SUB_STATUS,
            target=case,
            payload={"sub_status": self.sub_status.name, "status": CaseStatusEnum.get_text(self.status.status)},
        )

    def approve(self):
        from api.cases.notify import notify_exporter_licence_issued

        self.set_sub_status(CaseSubStatusIdEnum.FINALISED__APPROVED)
        notify_exporter_licence_issued(self)

    def refuse(self):
        from api.cases.notify import notify_exporter_licence_refused

        self.set_sub_status(CaseSubStatusIdEnum.FINALISED__REFUSED)
        notify_exporter_licence_refused(self)

    def no_licence_required(self):
        from api.cases.notify import notify_exporter_no_licence_required

        notify_exporter_no_licence_required(self)

    def move_case_forward(self, queue, user):
        from api.audit_trail import service as audit_trail_service
        from api.workflow.user_queue_assignment import user_queue_assignment_workflow

        assignments = (
            CaseAssignment.objects.select_related("queue").filter(case=self, queue=queue).order_by("queue__name")
        )

        # Unassign existing case advisors to be able to move forward
        if assignments:
            assignments.delete()

        # Run routing rules and move the case forward
        user_queue_assignment_workflow([queue], self)

        audit_trail_service.create(
            actor=user,
            verb=AuditType.UNASSIGNED_QUEUES,
            target=self,
            payload={"queues": [queue.name], "additional_text": ""},
        )

    @transaction.atomic
    def finalise(self, user, decisions, note):
        from api.audit_trail import service as audit_trail_service
        from api.cases.libraries.finalise import remove_flags_on_finalisation, remove_flags_from_audit_trail
        from api.licences.models import Licence

        try:
            licence = Licence.objects.get_draft_licence(self)
        except Licence.DoesNotExist:
            # This is not an error as there won't be a licence for refusal cases
            licence = None

        if AdviceType.APPROVE in decisions and licence:
            licence.decisions.set([Decision.objects.get(name=decision) for decision in decisions])

            logging.info("Initiate issue of licence %s (status: %s)", licence.reference_code, licence.status)
            licence.issue()

            if Licence.objects.filter(case=self).count() > 1:
                audit_trail_service.create(
                    actor=user,
                    verb=AuditType.REINSTATED_APPLICATION,
                    target=self,
                    payload={
                        "licence_duration": licence.duration,
                        "start_date": licence.start_date.strftime("%Y-%m-%d"),
                    },
                )

        # Finalise Case
        old_status = self.status.status
        self.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        self.save()

        audit_trail_service.create(
            actor=user,
            verb=AuditType.UPDATED_STATUS,
            target=self,
            payload={
                "status": {"new": self.status.status, "old": old_status},
                "additional_text": note,
            },
        )
        logging.info("Case is now finalised")

        decision_actions = self.get_decision_actions()
        for advice_type in decisions:

            decision_actions[advice_type](self)

            # NLR is not considered as licence decision
            if advice_type in [AdviceType.APPROVE, AdviceType.REFUSE]:
                decision = LicenceDecisionType.advice_type_to_decision(advice_type)
                previous_licence_decision = self.licence_decisions.last()

                previous_decision = None
                current_decision = decision
                if previous_licence_decision and decision == LicenceDecisionType.ISSUED:
                    # In case if it is being issued after an appeal then we want to reflect that in the decision
                    if previous_licence_decision.decision in [
                        LicenceDecisionType.REFUSED,
                        LicenceDecisionType.ISSUED_ON_APPEAL,
                    ]:
                        current_decision = LicenceDecisionType.ISSUED_ON_APPEAL

                    # link up to previous instance if the decision remains same
                    if previous_licence_decision.decision == current_decision:
                        previous_decision = previous_licence_decision

                licence_decision = LicenceDecision.objects.create(
                    case=self,
                    decision=current_decision,
                    licence=licence,
                    previous_decision=previous_decision,
                )
                if advice_type == AdviceType.REFUSE:
                    denial_reasons = (
                        self.advice.filter(
                            level=AdviceLevel.FINAL,
                            type=AdviceType.REFUSE,
                        )
                        .only("denial_reasons__id")
                        .distinct()
                        .values_list("denial_reasons__id", flat=True)
                    )
                    licence_decision.denial_reasons.set(denial_reasons)

            licence_reference = licence.reference_code if licence and advice_type == AdviceType.APPROVE else ""
            audit_trail_service.create(
                actor=user,
                verb=AuditType.CREATED_FINAL_RECOMMENDATION,
                target=self,
                payload={
                    "case_reference": self.reference_code,
                    "decision": advice_type,
                    "licence_reference": licence_reference,
                },
            )

        self.publish_decision_documents()

        # Remove Flags and related Audits when Finalising
        remove_flags_on_finalisation(self)
        remove_flags_from_audit_trail(self)

        return licence.id if licence else ""

    def publish_decision_documents(self):
        from api.cases.generated_documents.models import GeneratedCaseDocument

        documents = GeneratedCaseDocument.objects.filter(advice_type__isnull=False, case=self)
        documents.update(visible_to_exporter=True)
        for document in documents:
            document.send_exporter_notifications()

        logging.info("Licence documents published to exporter, notification sent")

    def delete(self, *args, **kwargs):
        # This simulates `models.SET_NULL` as a `GenericRelation`, which `audit_trail` is, implicitly does a cascased
        # delete.
        # Without doing this we would delete the audit trails associated to this case when this case is deleted and
        # we want to keep them.
        self.audit_trail.update(
            target_content_type=None,
            target_object_id=None,
        )
        return super().delete(*args, **kwargs)


class CaseQueue(TimestampableModel):
    case = models.ForeignKey(Case, related_name="casequeues", on_delete=models.DO_NOTHING)
    queue = models.ForeignKey(Queue, related_name="casequeues", on_delete=models.DO_NOTHING)

    class Meta:
        db_table = "cases_case_queues"


class CaseAssignmentSLA(models.Model):
    """
    Keeps track of days passed since case assigned to a team
    """

    sla_days = models.IntegerField()
    queue = models.ForeignKey(Queue, related_name="slas", on_delete=models.CASCADE)
    case = models.ForeignKey(Case, related_name="slas", on_delete=models.CASCADE)


class DepartmentSLA(models.Model):
    """
    Keeps track of days passed since application received in department
    """

    sla_days = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="department_slas")
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="department_slas")


class CaseReferenceCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_number = models.IntegerField()
    year = models.IntegerField(editable=False, unique=True)

    objects = CaseReferenceCodeManager()

    def __str__(self):
        return f"{self.year} {self.reference_number}"


class CaseNoteMentions(TimestampableModel):
    user = models.ForeignKey(GovUser, on_delete=models.DO_NOTHING, related_name="mentions")
    team = models.ForeignKey(Team, on_delete=models.DO_NOTHING, null=True, blank=True, related_name="mentions")
    case_note = models.ForeignKey("cases.CaseNote", on_delete=models.DO_NOTHING, related_name="mentions", default=None)
    is_accessed = models.BooleanField(default=False, help_text="indicates if a user has accessed this mention")


class CaseNote(TimestampableModel):
    """
    Note on a case, visible to internal users and exporters depending on is_visible_to_exporter.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, related_name="case_notes", on_delete=models.CASCADE)
    user = models.ForeignKey(
        BaseUser,
        related_name="case_notes",
        on_delete=models.CASCADE,
        default=None,
        null=False,
    )
    text = models.TextField(default=None, blank=True, null=True)
    is_visible_to_exporter = models.BooleanField(default=False, blank=False, null=False)

    notifications = GenericRelation(ExporterNotification, related_query_name="case_note")
    is_urgent = models.BooleanField(default=False, help_text="indicates if a case note mention is urgent")

    def save(self, *args, **kwargs):
        exporter_user = False
        if isinstance(self.user, ExporterUser) or ExporterUser.objects.filter(pk=self.user.pk).exists():
            self.is_visible_to_exporter = True
            exporter_user = True

        send_notification = not exporter_user and self.is_visible_to_exporter and self._state.adding
        super(CaseNote, self).save(*args, **kwargs)

        if send_notification:
            for user_relationship in UserOrganisationRelationship.objects.filter(organisation=self.case.organisation):
                user_relationship.send_notification(content_object=self, case=self.case)


class CaseAssignment(TimestampableModel):
    """
    Assigns users to a case on a particular queue
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="case_assignments")
    user = models.ForeignKey(GovUser, on_delete=models.CASCADE, related_name="case_assignments")
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name="case_assignments")

    class Meta:
        unique_together = [["case", "user", "queue"]]

    def save(self, *args, **kwargs):
        from api.audit_trail import service as audit_trail_service

        audit_user = None
        user = None
        audit_note = None

        if "audit_user" in kwargs:
            audit_user = kwargs.pop("audit_user")

        if "user" in kwargs:
            user = kwargs.pop("user")

        if "audit_note" in kwargs:
            audit_note = kwargs.pop("audit_note")

        super().save(*args, **kwargs)
        if audit_user and user:
            audit_trail_service.create(
                actor=audit_user,
                verb=AuditType.ASSIGN_USER_TO_CASE,
                action_object=self.case,
                payload={
                    "user": user.first_name + " " + user.last_name,
                    "queue": self.queue.name,
                    "additional_text": audit_note,
                },
            )


class CaseDocument(Document):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    user = models.ForeignKey(GovUser, on_delete=models.CASCADE, null=True)
    description = models.TextField(default=None, blank=True, null=True)
    type = models.CharField(
        choices=CaseDocumentState.choices, default=CaseDocumentState.UPLOADED, max_length=100, null=False
    )
    visible_to_exporter = models.BooleanField(blank=False, null=False)


class Advice(TimestampableModel):
    """
    Advice for goods and destinations on cases
    """

    ENTITY_FIELDS = ["good", "country", "end_user", "consignee", "ultimate_end_user", "third_party"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, related_name="advice", on_delete=models.CASCADE)
    user = models.ForeignKey(GovUser, on_delete=models.PROTECT)
    type = models.CharField(choices=AdviceType.choices, max_length=30)
    text = models.TextField(default=None, blank=True, null=True)
    note = models.TextField(default=None, blank=True, null=True)
    is_refusal_note = models.BooleanField(default=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True)
    level = models.CharField(choices=AdviceLevel.choices, max_length=30)

    # optional footnotes for advice
    footnote = models.TextField(blank=True, null=True, default=None)
    footnote_required = models.BooleanField(null=True, blank=True, default=None)

    # Optional goods/destinations
    good = models.ForeignKey("goods.Good", related_name="advice", on_delete=models.CASCADE, null=True)
    country = models.ForeignKey("countries.Country", related_name="advice", on_delete=models.CASCADE, null=True)
    end_user = models.ForeignKey("parties.Party", on_delete=models.CASCADE, null=True)
    ultimate_end_user = models.ForeignKey(
        "parties.Party", on_delete=models.CASCADE, related_name="ultimate_end_user", null=True
    )
    consignee = models.ForeignKey("parties.Party", on_delete=models.CASCADE, related_name="consignee", null=True)
    third_party = models.ForeignKey("parties.Party", on_delete=models.CASCADE, related_name="third_party", null=True)

    # Optional depending on type of advice
    proviso = models.TextField(default=None, blank=True, null=True)
    denial_reasons = models.ManyToManyField(DenialReason)
    pv_grading = models.CharField(choices=PvGrading.choices, null=True, max_length=30)
    # This is to store the collated security grading(s) for display purposes
    collated_pv_grading = models.TextField(default=None, blank=True, null=True)
    countersign_comments = models.TextField(
        blank=True,
        default="",
        help_text="Reasons provided by the countersigner when they agree/disagree with the advice during countersigning",
    )
    countersigned_by = models.ForeignKey(
        GovUser, on_delete=models.DO_NOTHING, related_name="countersigned_by", blank=True, null=True
    )

    objects = AdviceManager()

    class Meta:
        db_table = "advice"

    @property
    def entity_field(self):
        for field in self.ENTITY_FIELDS:
            entity = getattr(self, field, None)
            if entity:
                return field

    @property
    def entity(self):
        return getattr(self, self.entity_field, None)

    def save(self, *args, **kwargs):
        denial_reasons = None
        try:
            if self.level == AdviceLevel.TEAM:
                old_advice = Advice.objects.get(
                    case=self.case,
                    team=self.team,
                    level=AdviceLevel.TEAM,
                    good=self.good,
                    country=self.country,
                    end_user=self.end_user,
                    ultimate_end_user=self.ultimate_end_user,
                    consignee=self.consignee,
                    third_party=self.third_party,
                )
                denial_reasons = [denial_reason for denial_reason in old_advice.denial_reasons.all()]
                old_advice.delete()
            elif self.level == AdviceLevel.USER:
                old_advice = Advice.objects.get(
                    case=self.case,
                    good=self.good,
                    user=self.user,
                    team=self.user.team,
                    level=AdviceLevel.USER,
                    country=self.country,
                    end_user=self.end_user,
                    ultimate_end_user=self.ultimate_end_user,
                    consignee=self.consignee,
                    third_party=self.third_party,
                )
                denial_reasons = [denial_reason for denial_reason in old_advice.denial_reasons.all()]
                old_advice.delete()
        except Advice.DoesNotExist:
            pass

        has_no_team_set = self.team is None
        has_user = self.user is not None
        if has_no_team_set and has_user:
            self.team = self.user.team

        super(Advice, self).save(*args, **kwargs)

        # We retain the denial reasons from the previous object because we're effectively really doing an edit here by
        # removing the previous advice and create a new one in its place, however we lose the many-to-many relationship
        # the old object had so we reinstate it here.
        # This may look like it would overwrite the denial reasons that were set currently if you were editing this
        # object but if you were editing the denial reasons you'd first have to save this object and _then_ set the
        # denial reasons afterwards, so in that case this just gets overwritten anyway.
        # We do this after the save method as this object needs to have its id in place so we can create these
        # many-to-many objects.
        if denial_reasons:
            self.denial_reasons.set(denial_reasons)

    def equals(self, other):
        return all(
            [
                self.type == other.type,
                self.text == other.text,
                self.note == other.note,
                self.proviso == other.proviso,
                self.pv_grading == other.pv_grading,
                [x for x in self.denial_reasons.values_list()] == [x for x in other.denial_reasons.values_list()],
            ]
        )


class CountersignAdvice(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    valid = models.BooleanField(
        default=True,
        blank=True,
        null=True,
        help_text="Indicates whether it is valid or not. Existing countersignatures become invalid if original outcome is edited following countersigning comments. In this case we want to keep the CountersignAdvice object for audit but we do not want to consider this as valid advice anymore, hence we set `valid=False`.",  # noqa
    )
    order = models.PositiveIntegerField(help_text="Indicates countersigning order")
    outcome_accepted = models.BooleanField()
    reasons = models.TextField(
        help_text="Reasons provided by the countersigner when they agree/disagree with the advice during countersigning",
    )
    countersigned_user = models.ForeignKey(GovUser, on_delete=models.DO_NOTHING, related_name="countersigned_user")
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="countersign_advice")
    advice = models.ForeignKey(Advice, on_delete=models.CASCADE, related_name="countersign")


class EcjuQuery(TimestampableModel):
    """
    Query from ECJU to exporters
    """

    # Allows the properies to be queryable, allowing filters
    objects = QueryablePropertiesManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.CharField(null=False, blank=False, max_length=5000)
    response = models.CharField(null=True, blank=True, max_length=2200)
    case = models.ForeignKey(Case, related_name="case_ecju_query", on_delete=models.CASCADE)
    team = models.ForeignKey(Team, null=True, on_delete=models.CASCADE)
    responded_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    raised_by_user = models.ForeignKey(
        GovUser,
        related_name="raised_by_user_ecju_query",
        on_delete=models.CASCADE,
        default=None,
        null=False,
    )
    responded_by_user = models.ForeignKey(
        BaseUser,
        related_name="responded_by_user_ecju_query",
        on_delete=models.CASCADE,
        default=None,
        null=True,
    )
    query_type = models.CharField(
        choices=ECJUQueryType.choices, max_length=50, default=ECJUQueryType.ECJU, null=False, blank=False
    )
    chaser_email_sent_on = models.DateTimeField(blank=True, null=True)

    @queryable_property
    def is_query_closed(self):
        return self.responded_by_user is not None

    @queryable_property
    def is_manually_closed(self):
        if self.responded_by_user and self.responded_by_user.type == UserType.INTERNAL:
            return True
        else:
            return False

    # This method allows the above propery to be used in filtering objects. Similar to db fields.
    @is_query_closed.filter(lookups=("exact",))
    def is_query_closed(self, lookup, value):
        return ~Q(responded_by_user__isnull=value)

    @property
    def open_working_days(self):
        start_date = self.created_at
        end_date = self.responded_at if self.responded_at else timezone.now()
        return working_days_in_range(start_date=start_date, end_date=end_date)

    notifications = GenericRelation(ExporterNotification, related_query_name="ecju_query")

    def save(self, *args, **kwargs):
        existing_instance_count = EcjuQuery.objects.filter(id=self.id).count()

        # Only create a notification when saving a ECJU query for the first time
        if existing_instance_count == 0:
            super(EcjuQuery, self).save(*args, **kwargs)
            for user_relationship in UserOrganisationRelationship.objects.filter(organisation=self.case.organisation):
                user_relationship.send_notification(content_object=self, case=self.case)
        else:
            self.responded_at = timezone.now()
            super(EcjuQuery, self).save(*args, **kwargs)


class EcjuQueryDocument(Document):
    query = models.ForeignKey(EcjuQuery, on_delete=models.CASCADE, related_name="ecjuquery_document")
    user = models.ForeignKey(ExporterUser, on_delete=models.DO_NOTHING, related_name="ecjuquery_document")
    description = models.TextField(default="", blank=True)


class EnforcementCheckID(models.Model):
    """
    Enforcement XML doesn't support 64 bit ints (UUID's).
    So this mapping table maps entity uuid's to enforcement ids (32 bit)
    """

    id = models.AutoField(primary_key=True)
    entity_id = models.UUIDField(unique=True)
    entity_type = models.CharField(choices=EnforcementXMLEntityTypes.choices, max_length=20)


class LicenceDecision(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.DO_NOTHING, related_name="licence_decisions")
    decision = models.CharField(choices=LicenceDecisionType.choices, max_length=50, null=False, blank=False)
    licence = models.ForeignKey(
        "licences.Licence", on_delete=models.DO_NOTHING, related_name="licence_decisions", null=True, blank=True
    )
    denial_reasons = models.ManyToManyField(DenialReason)
    excluded_from_statistics_reason = models.TextField(default=None, blank=True, null=True)
    previous_decision = models.ForeignKey(
        "self", related_name="previous_decisions", default=None, null=True, on_delete=models.DO_NOTHING
    )

    class Meta:
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.case.reference_code} - {self.decision} ({self.created_at})"


class CaseQueueMovement(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, related_name="casequeuemovements", on_delete=models.DO_NOTHING)
    queue = models.ForeignKey(Queue, related_name="casequeuemovements", on_delete=models.DO_NOTHING)
    exit_date = models.DateTimeField(blank=True, null=True)
