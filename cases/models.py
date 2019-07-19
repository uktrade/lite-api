import uuid

import reversion
from django.db import models

from applications.models import Application
from documents.models import Document
from case_types.models import CaseType
from clc_queries.models import ClcQuery
from gov_users.models import GovUser
from queues.models import Queue


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


@reversion.register()
class CaseNote(models.Model):
    """
    Note on a case, visible by internal users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, related_name='case_note', on_delete=models.CASCADE)
    user = models.ForeignKey(GovUser, related_name='case_note', on_delete=models.CASCADE, default=None, null=False)
    text = models.TextField(default=None, blank=True, null=True, max_length=2200)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    is_visible_for_exporter = models.BooleanField(default=False, blank=True, null=True)

    # pylint: disable=W0221
    def save(self, *args, **kwargs):
        creating = self._state.adding is True
        super(CaseNote, self).save(*args, **kwargs)

        if creating and self.is_visible_for_exporter:
            if not self.case.clc_query:
                for user in self.case.application.organisation.user_set.all():
                    user.create_notification(self)
            else:
                for user in self.case.clc_query.good.organisation.user_set.all():
                    user.create_notification(self)


class CaseAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    users = models.ManyToManyField(GovUser, related_name='case_assignments')
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)


class CaseDocument(Document):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    user = models.ForeignKey(GovUser, on_delete=models.CASCADE)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
