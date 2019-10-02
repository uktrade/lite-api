from django.db import models


class LetterTemplate(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=30)  # document file name
    name = models.CharField(max_length=30)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.id
