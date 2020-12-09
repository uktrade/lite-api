from api.common.models import TimestampableModel
from api.users.models import GovUser

from django.db import models


class Comment(TimestampableModel):
    user = models.ForeignKey(GovUser, related_name="product_comments", on_delete=models.CASCADE)
    text = models.TextField()
    object_pk = models.TextField(help_text="The LITE or SPIRE product pk. Not the pk of this model instance")
    source = models.TextField(
        choices=(("SPIRE", "SPIRE"), ("LITE", "LITE")), help_text="Is the product from LITE or SPIRE?"
    )
