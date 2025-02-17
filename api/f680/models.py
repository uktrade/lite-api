from django.db import models

from api.applications.models import BaseApplication

from api.f680.managers import F680ApplicationQuerySet


class Hasher(dict):
    # https://stackoverflow.com/a/3405143/190597
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value


class F680Application(BaseApplication):  # /PS-IGNORE
    objects = F680ApplicationQuerySet.as_manager()

    application = models.JSONField()

    @property
    def application_dict(self):
        if not isinstance(self.application, dict):
            return Hasher({})
        return Hasher(self.application)

    def get_application_field_value(self, section, field_key):
        # TODO: investigate wrapping up accessing fields on application JSON with some OOP
        section_fields = self.application_dict["sections"][section]["fields"]
        for field in section_fields:
            if field["key"] == field_key:
                return field["raw_answer"]
        return None

    def on_submit(self):
        # TODO: Flesh out field promotion
        self.name = self.get_application_field_value("general_application_details", "name")
        self.save()
