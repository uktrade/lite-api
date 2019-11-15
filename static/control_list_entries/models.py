import uuid

from django.db import models


class ControlListEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rating = models.CharField(max_length=100, unique=True)
    text = models.TextField(blank=False, null=False)
    parent = models.ForeignKey(
        "self", default=None, null=True, on_delete=models.CASCADE
    )
    is_decontrolled = models.BooleanField(default=False)

    def __children(self):
        return ControlListEntry.objects.filter(parent=self)

    children = property(__children)

    @classmethod
    def create(cls, rating, text, parent, is_decontrolled):
        control_list_entry = cls(
            rating=rating, text=text, parent=parent, is_decontrolled=is_decontrolled
        )
        control_list_entry.save()
        return control_list_entry
