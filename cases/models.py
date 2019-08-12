import uuid

import reversion
from django.db import models

from applications.models import Application
from documents.models import Document
from case_types.models import CaseType
from clc_queries.models import ClcQuery
from queues.models import Queue
from users.models import BaseUser, ExporterUser, GovUser
from flags.models import Flag


@reversion.register()
class Case(models.Model):
    """
    Wrapper for application model intended for internal users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_type = models.ForeignKey(CaseType,
                                  related_name='case',
                                  on_delete=models.DO_NOTHING,
                                  default='0ec51727-2acf-4459-b568-93a906d84008')
    application = models.ForeignKey(Application, related_name='case', on_delete=models.CASCADE, null=True)
    clc_query = models.ForeignKey(ClcQuery, related_name='case', on_delete=models.CASCADE, null=True)
    queues = models.ManyToManyField(Queue, related_name='cases')
    flags = models.ManyToManyField(Flag, related_name='cases')


@reversion.register()
class CaseNote(models.Model):
    """
    Note on a case, visible by internal users.
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
