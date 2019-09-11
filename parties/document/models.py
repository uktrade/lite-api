from django.db import models

from documents.models import Document
from parties.models import EndUser, UltimateEndUser


class EndUserDocument(Document):
    end_user = models.ForeignKey(EndUser, on_delete=models.CASCADE)


class UltimateEndUserDocument(Document):
    ultimate_end_user = models.ForeignKey(UltimateEndUser, on_delete=models.CASCADE)
