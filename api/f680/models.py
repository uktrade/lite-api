from django.db import models
import uuid

from api.applications.models import BaseApplication
from api.organisations.models import Organisation
from api.staticdata.countries.models import Country

from api.f680.managers import F680ApplicationQuerySet
from api.f680 import enums


class F680Application(BaseApplication):  # /PS-IGNORE
    objects = F680ApplicationQuerySet.as_manager()

    application = models.JSONField()

    def get_application_field_value(self, section, field_key):
        # TODO: investigate wrapping up accessing fields on application JSON with some OOP
        #   we should be able to solve all the chained .gets() with a decent interface
        section_fields = self.application.get("sections", {}).get(section, {}).get("fields", [])
        for field in section_fields:
            if field.get("key") == field_key:
                return field.get("raw_answer")
        return None

    def on_submit(self):
        # TODO: Flesh out field promotion
        self.name = self.get_application_field_value("general_application_details", "name")
        self.save()


# TODO: Eventually we may want to use this model more widely.  We can do that
#   but for now baking it in to the f680 application avoids us having to guess
#   at unknown futures
class Recipient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    address = models.TextField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    type = models.CharField(choices=enums.RecipientType.choices, max_length=50)
    role = models.CharField(choices=enums.RecipientRole.choices, max_length=50, default=None, null=True)
    role_other = models.TextField(null=True, default=None)
    organisation = models.ForeignKey(Organisation, related_name="organisation_recipient", on_delete=models.CASCADE)


# TODO: Eventually we may want to use this model more widely.  We can do that
#   but for now baking it in to the f680 application avoids us having to guess
#   at unknown futures
class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField()
    security_grading = models.CharField(choices=enums.SecurityGrading.product_choices, max_length=50)
    security_grading_other = models.TextField(null=True, default=None)
    organisation = models.ForeignKey(Organisation, related_name="organisation_product", on_delete=models.CASCADE)


class SecurityRelease(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    application = models.ForeignKey(F680Application, on_delete=models.CASCADE)
    security_grading = models.CharField(choices=enums.SecurityGrading.security_release_choices, max_length=50)
    security_grading_other = models.TextField(null=True, default=None)
    # We need details of the release, this doesn't appear to be in the frontend flows yet..
    intended_use = models.TextField()
