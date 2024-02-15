from django.db import models


class ParentModel(models.Model):
    name = models.CharField(max_length=255)


class ChildModel(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(ParentModel, on_delete=models.CASCADE)
