import json

from django.apps import AppConfig

from content_strings import strings


class ContentStringsConfig(AppConfig):
    name = "content_strings"

    def ready(self):
        with open("lite-content/lite-api/strings.json") as json_file:
            strings.constants = json.load(json_file)
