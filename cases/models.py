import uuid

import reversion
from django.db import models
from rest_framework.exceptions import ValidationError

from applications.models import Application
from cases.enums import CaseType, AdviceType
from clc_queries.models import ClcQuery
from documents.models import Document
from end_user.models import EndUser
from flags.models import Flag
from goods.models import Good
from goodstype.models import GoodsType
from queues.models import Queue
from static.countries.models import Country
from static.denial_reasons.models import DenialReason
from users.models import BaseUser, ExporterUser, GovUser


@reversion.register()
class Case(models.Model):
    """
    Wrapper for application model intended for internal users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(choices=CaseType.choices, default=CaseType.APPLICATION, max_length=20)
    application = models.ForeignKey(Application, related_name='case', on_delete=models.CASCADE, null=True)
    clc_query = models.ForeignKey(ClcQuery, related_name='case', on_delete=models.CASCADE, null=True)
    queues = models.ManyToManyField(Queue, related_name='cases')
    flags = models.ManyToManyField(Flag, related_name='cases')


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

    # pylint: disable=W0221
    def save(self, *args, **kwargs):
        try:
            ExporterUser.objects.get(id=self.user.id)
            self.is_visible_to_exporter = True
        except ExporterUser.DoesNotExist:
            pass
        creating = self._state.adding is True
        super(CaseNote, self).save(*args, **kwargs)

        if creating and self.is_visible_to_exporter:
            organisation = self.case.clc_query.good.organisation if self.case.clc_query else self.case.application.organisation
            for user in ExporterUser.objects.filter(organisation=organisation):
                user.send_notification(self)


class CaseAssignment(models.Model):
    """
    Assigns users to a case on a particular queue
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    users = models.ManyToManyField(GovUser, related_name='case_assignments')
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)


class Notification(models.Model):
    user = models.ForeignKey(ExporterUser, on_delete=models.CASCADE, null=False)
    note = models.ForeignKey(CaseNote, on_delete=models.CASCADE, null=False)
    viewed_at = models.DateTimeField(null=True)


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

    # Optional goods/destinations
    good = models.ForeignKey(Good, on_delete=models.CASCADE, null=True)
    goods_type = models.ForeignKey(GoodsType, on_delete=models.CASCADE, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True)
    end_user = models.ForeignKey(EndUser, on_delete=models.CASCADE, null=True)
    ultimate_end_user = models.ForeignKey(EndUser, on_delete=models.CASCADE, related_name='ultimate_end_user', null=True)

    # Optional depending on type of advice
    proviso = models.TextField(default=None, blank=True, null=True)
    denial_reasons = models.ManyToManyField(DenialReason)

    # pylint: disable=W0221
    def save(self, *args, **kwargs):
        if self.type is not AdviceType.PROVISO:
            self.proviso = None

        try:
            existing_object = Advice.objects.get(case=self.case,
                                                 user=self.user,
                                                 good=self.good,
                                                 goods_type=self.goods_type,
                                                 country=self.country,
                                                 end_user=self.end_user,
                                                 ultimate_end_user=self.ultimate_end_user)
            existing_object.delete()
        except Advice.DoesNotExist:
            pass

        super(Advice, self).save(*args, **kwargs)

		
class EcjuQuery(models.Model):
    """
    Query from ECJU to exporters
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.CharField(null=False, blank=False, max_length=5000)
    response = models.CharField(null=True, blank=False, max_length=5000)
    case = models.ForeignKey(Case, related_name='case_ecju_query', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    raised_by_user = models.ForeignKey(GovUser, related_name='govuser_ecju_query', on_delete=models.CASCADE,
                                       default=None, null=False)
    responded_by_user = models.ForeignKey(ExporterUser, related_name='exportuser_ecju_query', on_delete=models.CASCADE,
                                          default=None, null=True)
