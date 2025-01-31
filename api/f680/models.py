from django.db import models
from api.applications.models import BaseApplication


class F680Application(BaseApplication):  # /PS-IGNORE
    application = models.JSONField()
