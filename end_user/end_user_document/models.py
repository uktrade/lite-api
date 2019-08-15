from django.db import models

from documents.models import Document
from drafts.models import Draft
from end_user.models import EndUser
from organisations.models import Organisation
from users.models import ExporterUser


class EndUserDocument(Document):
    end_user = models.ForeignKey(EndUser, on_delete=models.CASCADE)
    description = models.TextField(default=None, blank=True, null=True, max_length=280)
