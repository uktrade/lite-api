from django.core.management.base import BaseCommand
from django.core.management import call_command


apps = [
    "addresses",
    "applications",
    "audit_trail",
    "cases",
    "compliance",
    "documents",
    "flags",
    "goods",
    "goodstype",
    "letter_templates",
    "licences",
    "open_general_licences",
    "organisations",
    "parties",
    "picklists",
    "queries",
    "queues",
    "teams",
    "users",
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        for app in apps:
            call_command("graph_models", app, pygraphviz=True, output=f"docs/entity-relation-diagrams/{app}.png")
        self.stdout.write(self.style.SUCCESS("ER diagrams outputted to docs/entity-relation-diagrams/"))
