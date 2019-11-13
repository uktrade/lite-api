import json

from django.apps import AppConfig

from content_strings import strings


class ContentStringsConfig(AppConfig):
    name = 'content_strings'

    def ready(self):
        with open('lite_content/lite-api/strings.json') as json_file:
            strings.values = json.load(json_file)
