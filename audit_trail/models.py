from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timesince
from django.utils.translation import ugettext as _

from audit_trail.managers import AuditManager
from common.models import TimestampableModel


class Audit(TimestampableModel):
    """
    """
    actor_content_type = models.ForeignKey(
        ContentType, related_name='actor', null=True,
        on_delete=models.SET_NULL, db_index=True,
    )
    actor_object_id = models.CharField(max_length=255, db_index=True, null=True)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    verb = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)

    target_content_type = models.ForeignKey(
        ContentType, blank=True, null=True,
        related_name='target',
        on_delete=models.SET_NULL, db_index=True
    )
    target_object_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    target = GenericForeignKey(
        'target_content_type',
        'target_object_id'
    )

    action_object_content_type = models.ForeignKey(
        ContentType, blank=True, null=True,
        related_name='action_object',
        on_delete=models.SET_NULL, db_index=True
    )
    action_object_object_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    action_object = GenericForeignKey(
        'action_object_content_type',
        'action_object_object_id'
    )

    payload = JSONField()

    objects = AuditManager()

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        ctx = {
            'actor': self.actor,
            'verb': self.verb,
            'action_object': self.action_object,
            'target': self.target,
            'age': self.age()
        }
        if self.target:
            if self.action_object:
                return _('%(actor)s %(verb)s %(action_object)s on %(target)s %(age)s ago') % ctx
            return _('%(actor)s %(verb)s %(target)s %(age)s ago') % ctx
        if self.action_object:
            return _('%(actor)s %(verb)s %(action_object)s %(age)s ago') % ctx
        return _('%(actor)s %(verb)s %(age)s ago') % ctx

    def age(self):
        return timesince.timesince(self.created_at).encode('utf8').replace(b'\xc2\xa0', b' ').decode('utf8')
