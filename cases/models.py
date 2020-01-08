import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from cases.enums import CaseTypeEnum, AdviceType, CaseDocumentState
from cases.managers import CaseManager
from common.models import TimestampableModel
from documents.models import Document
from flags.models import Flag
from organisations.models import Organisation
from parties.models import EndUser, UltimateEndUser, Consignee, ThirdParty
from queues.models import Queue
from static.countries.models import Country
from static.denial_reasons.models import DenialReason
from static.statuses.models import CaseStatus
from teams.models import Team
from users.models import (
    BaseUser,
    ExporterUser,
    GovUser,
    UserOrganisationRelationship,
    ExporterNotification,
)


class Case(TimestampableModel):
    """
    Base model for applications and queries
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(choices=CaseTypeEnum.choices, max_length=35)
    queues = models.ManyToManyField(Queue, related_name="cases")
    flags = models.ManyToManyField(Flag, related_name="cases")
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(blank=True, null=True)
    status = models.ForeignKey(
        CaseStatus, related_name="query_status", on_delete=models.CASCADE, blank=True, null=True,
    )
    case_officer = models.ForeignKey(GovUser, null=True, on_delete=models.DO_NOTHING)

    objects = CaseManager()

    def get_case(self):
        """
        For any child models, this method allows easy access to the parent Case.

        Child cases [StandardApplication, OpenApplication, ...] share `id` with Case.
        """
        if type(self) == Case:
            return self

        return Case.objects.get(id=self.id)


class CaseNote(TimestampableModel):
    """
    Note on a case, visible to internal users and exporters depending on is_visible_to_exporter.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, related_name="case_note", on_delete=models.CASCADE)
    user = models.ForeignKey(BaseUser, related_name="case_note", on_delete=models.CASCADE, default=None, null=False,)
    text = models.TextField(default=None, blank=True, null=True, max_length=2200)
    is_visible_to_exporter = models.BooleanField(default=False, blank=False, null=False)

    notifications = GenericRelation(ExporterNotification, related_query_name="case_note")

    def save(self, *args, **kwargs):
        exporter_user = False
        if isinstance(self.user, ExporterUser) or ExporterUser.objects.filter(id=self.user.id).exists():
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
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    users = models.ManyToManyField(GovUser, related_name="case_assignments")
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)


class CaseDocument(Document):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    user = models.ForeignKey(GovUser, on_delete=models.CASCADE)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
    type = models.CharField(
        choices=CaseDocumentState.choices, default=CaseDocumentState.UPLOADED, max_length=100, null=False
    )


class Advice(TimestampableModel):
    """
    Advice for goods and destinations on cases
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    user = models.ForeignKey(GovUser, on_delete=models.PROTECT)
    type = models.CharField(choices=AdviceType.choices, max_length=30)
    text = models.TextField(default=None, blank=True, null=True)
    note = models.TextField(default=None, blank=True, null=True)

    # Optional goods/destinations
    good = models.ForeignKey("goods.Good", on_delete=models.CASCADE, null=True)
    goods_type = models.ForeignKey("goodstype.GoodsType", on_delete=models.CASCADE, null=True)
    country = models.ForeignKey("countries.Country", on_delete=models.CASCADE, null=True)
    end_user = models.ForeignKey(EndUser, on_delete=models.CASCADE, null=True)
    ultimate_end_user = models.ForeignKey(
        UltimateEndUser, on_delete=models.CASCADE, related_name="ultimate_end_user", null=True,
    )
    consignee = models.ForeignKey(Consignee, on_delete=models.CASCADE, related_name="consignee", null=True)
    third_party = models.ForeignKey(ThirdParty, on_delete=models.CASCADE, related_name="third_party", null=True)

    # Optional depending on type of advice
    proviso = models.TextField(default=None, blank=True, null=True)
    denial_reasons = models.ManyToManyField(DenialReason)

    def save(self, *args, **kwargs):
        if self.type != AdviceType.PROVISO and self.type != AdviceType.CONFLICTING:
            self.proviso = None

        try:
            existing_object = Advice.objects.get(
                case=self.case,
                user=self.user,
                good=self.good,
                goods_type=self.goods_type,
                country=self.country,
                end_user=self.end_user,
                ultimate_end_user=self.ultimate_end_user,
                consignee=self.consignee,
                third_party=self.third_party,
            )
            existing_object.delete()
        except Advice.DoesNotExist:
            pass

        super(Advice, self).save(*args, **kwargs)


class TeamAdvice(Advice):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    # pylint: disable=W0221
    # pylint: disable=E1003
    def save(self, *args, **kwargs):

        if self.type != AdviceType.PROVISO and self.type != AdviceType.CONFLICTING:
            self.proviso = None

        try:
            existing_object = TeamAdvice.objects.get(
                case=self.case,
                team=self.team,
                good=self.good,
                goods_type=self.goods_type,
                country=self.country,
                end_user=self.end_user,
                ultimate_end_user=self.ultimate_end_user,
                consignee=self.consignee,
                third_party=self.third_party,
            )
            existing_object.delete()
        except TeamAdvice.DoesNotExist:
            pass

        # We override the parent class save() method so we only delete existing team level objects
        super(Advice, self).save(*args, **kwargs)


class FinalAdvice(Advice):
    # pylint: disable=W0221
    # pylint: disable=E1003
    def save(self, *args, **kwargs):

        if self.type != AdviceType.PROVISO and self.type != AdviceType.CONFLICTING:
            self.proviso = None

        try:
            existing_object = FinalAdvice.objects.get(
                case=self.case,
                good=self.good,
                goods_type=self.goods_type,
                country=self.country,
                end_user=self.end_user,
                ultimate_end_user=self.ultimate_end_user,
                consignee=self.consignee,
                third_party=self.third_party,
            )
            existing_object.delete()
        except FinalAdvice.DoesNotExist:
            pass

        # We override the parent class save() method so we only delete existing final level objects
        super(Advice, self).save(*args, **kwargs)


class EcjuQuery(TimestampableModel):
    """
    Query from ECJU to exporters
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.CharField(null=False, blank=False, max_length=5000)
    response = models.CharField(null=True, blank=False, max_length=2200)
    case = models.ForeignKey(Case, related_name="case_ecju_query", on_delete=models.CASCADE)
    responded_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    raised_by_user = models.ForeignKey(
        GovUser, related_name="govuser_ecju_query", on_delete=models.CASCADE, default=None, null=False,
    )
    responded_by_user = models.ForeignKey(
        ExporterUser, related_name="exportuser_ecju_query", on_delete=models.CASCADE, default=None, null=True,
    )

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


class GoodCountryDecision(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    good = models.ForeignKey("goodstype.GoodsType", on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    decision = models.CharField(choices=AdviceType.choices, max_length=30)

    def save(self, *args, **kwargs):
        GoodCountryDecision.objects.filter(case=self.case, good=self.good, country=self.country).delete()

        super(GoodCountryDecision, self).save(*args, **kwargs)


class CaseType(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=30)
    name = models.CharField(choices=CaseTypeEnum.choices, null=False, max_length=35)
