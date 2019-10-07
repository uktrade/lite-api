from django.db import models


class LetterLayout(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=30)  # letter file name minus extension
    name = models.CharField(max_length=30)  # friendly name

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.id
