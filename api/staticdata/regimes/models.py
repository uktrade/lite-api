import uuid

from django.db import models


class Regime(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    def __repr__(self):
        return self.name


class RegimeSubsection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    regime = models.ForeignKey(
        Regime,
        on_delete=models.CASCADE,
        related_name="subsections",
    )

    def __repr__(self):
        return f"{self.regime} - {self.name}"


class RegimeEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    shortened_name = models.CharField(max_length=5, null=True)
    subsection = models.ForeignKey(
        RegimeSubsection,
        on_delete=models.CASCADE,
        related_name="entries",
    )

    def __repr__(self):
        return f"{self.subsection} - {self.name}"
