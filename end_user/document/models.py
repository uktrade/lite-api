from django.db import models

from documents.models import Document
from end_user.models import EndUser


class EndUserDocument(Document):
    end_user = models.ForeignKey(EndUser, on_delete=models.CASCADE)
