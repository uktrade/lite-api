from django.db import models

from api.applications.models import BaseApplication

from api.f680.managers import F680ApplicationQuerySet


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
