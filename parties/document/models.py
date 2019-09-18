from django.db import models

from documents.models import Document
from parties.models import Party


class PartyDocument(Document):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
