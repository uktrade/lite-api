import uuid

import reversion
from django.db import models

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
    user = models.ForeignKey(GovUser, on_delete=models.CASCADE)
    type = models.CharField(choices=AdviceType.choices, max_length=30)
    advice = models.TextField(default=None, blank=True, null=True)
    note = models.TextField(default=None, blank=True, null=True)

    # Optional goods
    goods = models.ManyToManyField(Good, related_name='goods')
    goods_types = models.ManyToManyField(GoodsType, related_name='goods_types')

    # Optional destinations
    countries = models.ManyToManyField(Country, related_name='countries')
    end_user = models.ForeignKey(EndUser, on_delete=models.CASCADE, null=True, blank=True)
    ultimate_end_users = models.ManyToManyField(EndUser, related_name='ultimate_end_users')

    # Optional depending on type of advice
    proviso = models.TextField(default=None, blank=True, null=True)
    denial_reasons = models.ManyToManyField(DenialReason)

    # pylint: disable=W0221
    def save(self, update_other_items=False, *args, **kwargs):
        if self.type is not AdviceType.PROVISO:
            self.proviso = None

        other_advice_on_case = Advice.objects.filter(case=self.case, user=self.user).exclude(pk=self.id)

        super(Advice, self).save(*args, **kwargs)

        if update_other_items:
            # Update other advice on this case by the same user
            other_advice_on_case = [advice for advice in other_advice_on_case if
                                    self.goods in advice.goods.all() or
                                    self.goods_types in advice.goods_types.all() or
                                    self.countries in advice.countries.all() or
                                    self.end_user is self.end_user or
                                    self.ultimate_end_users in advice.ultimate_end_users.all()]

            for advice in other_advice_on_case:
                advice.goods.remove(*self.goods.all())
                advice.goods_types.remove(*self.goods_types.all())
                advice.countries.remove(*self.countries.all())
                advice.ultimate_end_users.remove(*self.ultimate_end_users.all())

                if self.end_user:
                    advice.end_user = None

                advice.save()

                # Delete the advice if it isn't linked to anything
                if not advice.ultimate_end_users.all() and \
                        not advice.end_user and \
                        not advice.goods_types.all() and \
                        not advice.goods.all() and \
                        not advice.countries.all():
                    advice.delete()
