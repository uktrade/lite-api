from django.db import models

from api.applications.models import BaseApplication

from api.f680.managers import F680ApplicationQuerySet


class F680Application(BaseApplication):  # /PS-IGNORE
    objects = F680ApplicationQuerySet.as_manager()

    application = models.JSONField()
