import re
import uuid

import reversion
from django.db import models
from django.db.models.functions import Coalesce
from django.utils import timezone

from applications.models import BaseApplication
from cases.enums import CaseType, AdviceType
from cases.libraries.activity_types import CaseActivityType, BaseActivityType
from documents.models import Document
from parties.models import EndUser, UltimateEndUser, Consignee, ThirdParty
from flags.models import Flag
from goods.models import Good
from goodstype.models import GoodsType
from queries.models import Query
from queues.models import Queue
from static.countries.models import Country
from static.denial_reasons.models import DenialReason
from teams.models import Team
from users.models import BaseUser, ExporterUser, GovUser, UserOrganisationRelationship


@reversion.register()
class Case(models.Model):
    """
    Wrapper for application and query model intended for internal users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(choices=CaseType.choices, default=CaseType.APPLICATION, max_length=35)
    application = models.ForeignKey(BaseApplication, related_name='case', on_delete=models.CASCADE, null=True)
    query = models.ForeignKey(Query, related_name='case', on_delete=models.CASCADE, null=True)
    queues = models.ManyToManyField(Queue, related_name='cases')
    flags = models.ManyToManyField(Flag, related_name='cases')

    class Meta:
        ordering = [Coalesce('application__submitted_at', 'query__submitted_at')]


@reversion.register()
class CaseNote(models.Model):
    """
    Note on a case, visible to internal users and exporters depending on is_visible_to_exporter.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, related_name='case_note', on_delete=models.CASCADE)
    user = models.ForeignKey(BaseUser, related_name='case_note', on_delete=models.CASCADE, default=None, null=False)
    text = models.TextField(default=None, blank=True, null=True, max_length=2200)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    is_visible_to_exporter = models.BooleanField(default=False, blank=False, null=False)

    def save(self, *args, **kwargs):
        try:
            ExporterUser.objects.get(id=self.user.id)
            self.is_visible_to_exporter = True
        except ExporterUser.DoesNotExist:
            pass
        creating = self._state.adding is True
        super(CaseNote, self).save(*args, **kwargs)

        if creating and self.is_visible_to_exporter:
            organisation = self.case.query.organisation if self.case.query else self.case.application.organisation
            for user_relationship in UserOrganisationRelationship.objects.filter(organisation=organisation):
                user_relationship.user.send_notification(case_note=self)


class CaseAssignment(models.Model):
    """
    Assigns users to a case on a particular queue
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    users = models.ManyToManyField(GovUser, related_name='case_assignments')
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)


class CaseDocument(Document):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    user = models.ForeignKey(GovUser, on_delete=models.CASCADE)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)


class Advice(models.Model):
    """
    Advice for goods and destinations on cases
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    user = models.ForeignKey(GovUser, on_delete=models.PROTECT)
    type = models.CharField(choices=AdviceType.choices, max_length=30)
    text = models.TextField(default=None, blank=True, null=True)
    note = models.TextField(default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    # Optional goods/destinations
    good = models.ForeignKey(Good, on_delete=models.CASCADE, null=True)
    goods_type = models.ForeignKey(GoodsType, on_delete=models.CASCADE, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True)
    end_user = models.ForeignKey(EndUser, on_delete=models.CASCADE, null=True)
    ultimate_end_user = models.ForeignKey(UltimateEndUser, on_delete=models.CASCADE, related_name='ultimate_end_user',
                                          null=True)
    consignee = models.ForeignKey(Consignee, on_delete=models.CASCADE, related_name='consignee',
                                  null=True)
    third_party = models.ForeignKey(ThirdParty, on_delete=models.CASCADE, related_name='third_party',
                                    null=True)

    # Optional depending on type of advice
    proviso = models.TextField(default=None, blank=True, null=True)
    denial_reasons = models.ManyToManyField(DenialReason)

    def save(self, *args, **kwargs):
        if self.type != AdviceType.PROVISO and self.type != AdviceType.CONFLICTING:
            self.proviso = None

        try:
            existing_object = Advice.objects.get(case=self.case,
                                                 user=self.user,
                                                 good=self.good,
                                                 goods_type=self.goods_type,
                                                 country=self.country,
                                                 end_user=self.end_user,
                                                 ultimate_end_user=self.ultimate_end_user,
                                                 consignee=self.consignee,
                                                 third_party=self.third_party)
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
            existing_object = TeamAdvice.objects.get(case=self.case,
                                                     team=self.team,
                                                     good=self.good,
                                                     goods_type=self.goods_type,
                                                     country=self.country,
                                                     end_user=self.end_user,
                                                     ultimate_end_user=self.ultimate_end_user,
                                                     consignee=self.consignee,
                                                     third_party=self.third_party)
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
            existing_object = FinalAdvice.objects.get(case=self.case,
                                                      good=self.good,
                                                      goods_type=self.goods_type,
                                                      country=self.country,
                                                      end_user=self.end_user,
                                                      ultimate_end_user=self.ultimate_end_user,
                                                      consignee=self.consignee,
                                                      third_party=self.third_party)
            existing_object.delete()
        except FinalAdvice.DoesNotExist:
            pass

        # We override the parent class save() method so we only delete existing final level objects
        super(Advice, self).save(*args, **kwargs)


class EcjuQuery(models.Model):
    """
    Query from ECJU to exporters
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.CharField(null=False, blank=False, max_length=5000)
    response = models.CharField(null=True, blank=False, max_length=2200)
    case = models.ForeignKey(Case, related_name='case_ecju_query', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    responded_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    raised_by_user = models.ForeignKey(GovUser, related_name='govuser_ecju_query', on_delete=models.CASCADE,
                                       default=None, null=False)
    responded_by_user = models.ForeignKey(ExporterUser, related_name='exportuser_ecju_query', on_delete=models.CASCADE,
                                          default=None, null=True)

    def save(self, *args, **kwargs):
        existing_instance_count = EcjuQuery.objects.filter(id=self.id).count()

        # Only create a notification when saving a ECJU query for the first time
        if existing_instance_count == 0:
            super(EcjuQuery, self).save(*args, **kwargs)
            organisation = self.case.query.organisation if self.case.query else self.case.application.organisation
            for user_relationship in UserOrganisationRelationship.objects.filter(organisation=organisation):
                user_relationship.user.send_notification(ecju_query=self)
        else:
            self.responded_at = timezone.now()
            super(EcjuQuery, self).save(*args, **kwargs)


class Notification(models.Model):
    user = models.ForeignKey(BaseUser, on_delete=models.CASCADE, null=False)
    case_note = models.ForeignKey(CaseNote, on_delete=models.CASCADE, null=True)
    query = models.ForeignKey(Query, on_delete=models.CASCADE, null=True)
    ecju_query = models.ForeignKey(EcjuQuery, on_delete=models.CASCADE, null=True)
    viewed_at = models.DateTimeField(null=True)


class BaseActivity(models.Model):
    text = models.TextField(default=None)
    additional_text = models.TextField(default=None, null=True)
    user = models.ForeignKey(BaseUser, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    type = models.CharField(max_length=50)
    activity_types = BaseActivityType

    @classmethod
    def _replace_placeholders(cls, activity_type, **kwargs):
        """
        Replaces placeholders in activity_type with parameters given
        """
        # Get the placeholder for the supplied activity_type
        text = cls.activity_types.get_text(activity_type)
        placeholders = re.findall('{(.+?)}', text)

        # Raise an exception if the wrong amount of kwargs are given
        if len(placeholders) != len(kwargs):
            raise Exception('Incorrect number of values for activity_type, expected ' +
                            str(len(placeholders)) + ', got ' + str(len(kwargs)))

        # Raise an exception if all the placeholder parameters are not provided
        for placeholder in placeholders:
            if placeholder not in kwargs:
                raise Exception(f'{placeholder} not provided in parameters for activity type: {activity_type}')

        # Loop over kwargs, if type is list, convert to comma delimited string
        for key, value in kwargs.items():
            if isinstance(value, list):
                kwargs[key] = ', '.join(value)

        # Format text by replacing the placeholders with values using kwargs given
        text = text.format(**kwargs)

        # Add a full stop unless the text ends with a colon
        if not text.endswith(':') and not text.endswith('?'):
            text = text + '.'

        return text

    @classmethod
    def create(cls, activity_type, case, user, additional_text=None, created_at=None, save_object=True, **kwargs):
        # If activity_type isn't valid, raise an exception
        if activity_type not in [x[0] for x in cls.activity_types.choices]:
            raise Exception(f'{activity_type} isn\'t in ' + cls.activity_types.__name__)

        text = cls._replace_placeholders(activity_type, **kwargs)

        activity = cls(type=activity_type,
                       text=text,
                       user=user,
                       case=case,
                       additional_text=additional_text,
                       created_at=created_at)
        if save_object:
            activity.save()
        return activity


class CaseActivity(BaseActivity):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, null=False)
    activity_types = CaseActivityType


class GoodCountryDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    good = models.ForeignKey(GoodsType, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    decision = models.CharField(choices=AdviceType.choices, max_length=30)

    def save(self, *args, **kwargs):
        GoodCountryDecision.objects.filter(case=self.case,
                                           good=self.good,
                                           country=self.country).delete()

        super(GoodCountryDecision, self).save(*args, **kwargs)
