from django.db import models

from users.enums import UserType


class InternalManager(models.Manager):
    def get_queryset(self):
        return super(InternalManager, self).get_queryset().filter(type=UserType.INTERNAL)


class ExporterManager(models.Manager):
    def get_queryset(self):
        return super(ExporterManager, self).get_queryset().filter(type=UserType.EXPORTER)
