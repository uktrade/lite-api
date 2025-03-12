import uuid

from django.db import models
from django.contrib.postgres.fields import ArrayField

from api.applications.models import BaseApplication
from api.organisations.models import Organisation
from api.staticdata.countries.models import Country

from api.f680.managers import F680ApplicationQuerySet
from api.f680 import enums


class F680Application(BaseApplication):  # /PS-IGNORE
    objects = F680ApplicationQuerySet.as_manager()

    application = models.JSONField()

    def get_field_value(self, fields, field_key, raise_exception=True):
        for field in fields:
            if field.get("key") == field_key:
                return field.get("raw_answer")
        if raise_exception:
            raise KeyError(f"Field {field_key} not found in fields for application {self.id}")
        return None

    def get_application_field_value(self, section, field_key, raise_exception=True):
        section_fields = self.application["sections"][section]["fields"]
        return self.get_field_value(section_fields, field_key, raise_exception=raise_exception)

    def on_submit(self):
        self.name = self.get_application_field_value("general_application_details", "name")
        self.save()

        # Create the Product for this application - F680s just have the one
        product = Product.objects.create(
            name=self.get_application_field_value("product_information", "product_name"),
            description=self.get_application_field_value("product_information", "product_description"),
            organisation=self.organisation,
            security_grading=self.get_application_field_value(
                "product_information", "security_classification", raise_exception=False
            ),
        )

        # Create a Recipient and SecurityRelease for each.  In F680s caseworkers
        #   will advise against SecurityRelease records
        for item in self.application["sections"]["user_information"]["items"]:
            item_fields = item["fields"]

            recipient = Recipient.objects.create(
                name=self.get_field_value(item_fields, "end_user_name"),
                address=self.get_field_value(item_fields, "address"),
                country_id=self.get_field_value(item_fields, "country"),
                type=self.get_field_value(item_fields, "entity_type"),
                organisation=self.organisation,
                role=self.get_field_value(item_fields, "third_party_role", raise_exception=False),
                role_other=self.get_field_value(item_fields, "third_party_role_other", raise_exception=False),
            )

            SecurityReleaseRequest.objects.create(
                id=item["id"],  # Use the JSON item ID for the security release so we can tally the two easily later
                recipient=recipient,
                product=product,
                application=self,
                security_grading=self.get_field_value(item_fields, "security_classification"),
                intended_use=self.get_field_value(item_fields, "end_user_intended_end_use"),
                security_grading_other=self.get_field_value(
                    item_fields, "other_security_classification", raise_exception=False
                ),
                approval_types=self.get_application_field_value("approval_type", "approval_choices"),
            )


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
    security_grading = models.CharField(
        choices=enums.SecurityGrading.product_choices, max_length=50, null=True, default=None
    )
    security_grading_other = models.TextField(null=True, default=None)
    organisation = models.ForeignKey(Organisation, related_name="organisation_product", on_delete=models.CASCADE)


class SecurityReleaseRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    application = models.ForeignKey(F680Application, on_delete=models.CASCADE, related_name="security_releases")
    security_grading = models.CharField(choices=enums.SecurityGrading.security_release_choices, max_length=50)
    security_grading_other = models.TextField(null=True, default=None)
    approval_types = ArrayField(models.CharField(choices=enums.ApprovalTypes.choices, max_length=50))
    # We need details of the release, this doesn't appear to be in the frontend flows yet..
    intended_use = models.TextField()
