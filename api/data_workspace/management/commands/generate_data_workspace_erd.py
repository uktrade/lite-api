import inspect
import re
import sys

from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings
from django.template import Context
from django.template.engine import Engine

from rest_framework.viewsets import (
    GenericViewSet,
    ViewSet,
)


ERD_PATH = Path(settings.BASE_DIR) / "data_workspace" / "erd.mermaid"
TEMPLATE_DIRECTORY = Path(__file__).resolve().parent / "templates"


def is_viewset(m):
    return inspect.isclass(m) and issubclass(m, (GenericViewSet, ViewSet))


def convert(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class DiagramConfigError(Exception):
    pass


class TableMeta:
    def __init__(self, viewset_cls):
        self.skip = viewset_cls.__name__.startswith("Base")
        self.table_name = None

        if not self.skip:
            meta = getattr(viewset_cls, "DataWorkspace", None)
            if not meta:
                raise DiagramConfigError(f"You must declare a DataWorkspace class in your ViewSet {viewset_cls}")
            self.skip = getattr(meta, "skip", self.skip)
            self.table_name = getattr(meta, "table_name", None)
            if not self.table_name:
                raise DiagramConfigError(f"You must declare a table_name in your DataWorkspace class for {viewset_cls}")


class Table:
    def __init__(self, viewset_name, viewset_cls, meta):
        self.viewset_name = viewset_name
        self.viewset_cls = viewset_cls
        self.meta = meta

    @property
    def name(self):
        if self.meta.table_name:
            return self.meta.table_name

        name = self.viewset_name.replace("ViewSet", "")
        name = convert(name)
        name = name.lower()
        name = f"{name}s"

        return name


class Command(BaseCommand):
    def handle(self, *args, **options):
        viewsets = inspect.getmembers(sys.modules["api.data_workspace.v2.views"], is_viewset)

        tables = []
        for name, cls in viewsets:
            meta = TableMeta(cls)
            if meta.skip:
                continue
            tables.append(Table(name, cls, meta))

        engine = Engine(dirs=[TEMPLATE_DIRECTORY])
        template_name = "erd.mermaid"
        template = engine.get_template(template_name)
        rendered = template.render(Context({"tables": tables}))

        ERD_PATH.write_text(rendered)

        self.stdout.write(self.style.SUCCESS("ER diagrams outputted to docs/entity-relation-diagrams/"))
