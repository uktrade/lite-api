from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone, timesince

from audit_trail.managers import AuditManager


class Audit(models.Model):
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
        ordering = ('-timestamp',)

    def __str__(self):
        ctx = {
            'actor': self.actor,
            'verb': self.verb,
            'action_object': self.action_object,
            'target': self.target,
            'timesince': self.timesince()
        }
        if self.target:
            if self.action_object:
                return _('%(actor)s %(verb)s %(action_object)s on %(target)s %(timesince)s ago') % ctx
            return _('%(actor)s %(verb)s %(target)s %(timesince)s ago') % ctx
        if self.action_object:
            return _('%(actor)s %(verb)s %(action_object)s %(timesince)s ago') % ctx
        return _('%(actor)s %(verb)s %(timesince)s ago') % ctx

    def timesince(self, now=None):
        """
        Shortcut for the ``django.utils.timesince.timesince`` function of the
        current timestamp.
        """
        return timesince.timesince(self.timestamp, now).encode('utf8').replace(b'\xc2\xa0', b' ').decode('utf8')
