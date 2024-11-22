import datetime
import typing

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView

from django.urls import (
    NoReverseMatch,
    path,
)


class TableMetadataView(APIView):
    _ignore_model_permissions = True
    schema = None  # exclude from schema
    metadata = None

    def get(self, request, *args, **kwargs):
        tables = []
        namespace = request.resolver_match.namespace
        for table_metadata in self.metadata:
            url_name = table_metadata["endpoint"]
            if namespace:
                url_name = f"{namespace}:{url_name}"
            try:
                url = reverse(
                    url_name,
                    args=args,
                    kwargs=kwargs,
                    request=request,
                )
            except NoReverseMatch:
                # Don't bail out if eg. no list routes exist, only detail routes.
                continue

            tables.append(
                {
                    "table_name": table_metadata["table_name"],
                    "endpoint": url,
                    "indexes": table_metadata["indexes"],
                    "fields": table_metadata["fields"],
                }
            )
        return Response({"tables": tables})


def is_optional(field):
    return typing.get_origin(field) is typing.Union and type(None) in typing.get_args(field)


def get_fields(view):
    try:
        serializer = view.get_serializer()
    except AttributeError:
        return []

    primary_key_field = getattr(view.DataWorkspace, "primary_key", "id")

    fields = []
    for field in serializer.fields.values():
        if isinstance(field, serializers.HiddenField):
            continue

        field_metadata = {"name": field.field_name}
        if field.field_name == primary_key_field:
            field_metadata["primary_key"] = True

        if isinstance(field, serializers.UUIDField):
            field_metadata["type"] = "UUID"
            if field.allow_null:
                field_metadata["nullable"] = True

        elif isinstance(field, serializers.CharField):
            field_metadata["type"] = "String"
            if field.allow_null:
                field_metadata["nullable"] = True

        elif isinstance(field, serializers.SerializerMethodField):
            method = getattr(field.parent, field.method_name)
            return_type = method.__annotations__["return"]

            if is_optional(return_type):
                field_metadata["nullable"] = True
                return_type, _ = typing.get_args(return_type)

            if return_type is str:
                field_metadata["type"] = "String"
            elif return_type is datetime.datetime:
                field_metadata["type"] = "DateTime"
            else:  # pragma: no cover
                raise NotImplementedError(
                    f"Return type of {return_type} for {serializer.__class__.__name__}.{field.method_name} not handled"
                )

        elif isinstance(field, serializers.FloatField):
            field_metadata["type"] = "Float"
            if field.allow_null:
                field_metadata["nullable"] = True

        else:  # pragma: no cover
            raise NotImplementedError(f"Annotation not found for {field}")

        fields.append(field_metadata)
    return fields


class TableMetadataRouter(DefaultRouter):
    def register(self, viewset):
        if not hasattr(viewset, "DataWorkspace"):  # pragma: no cover
            raise NotImplementedError(f"No DataWorkspace configuration found for {viewset}")

        prefix = viewset.DataWorkspace.table_name.replace("_", "-")
        basename = f"dw-{prefix}"

        super().register(prefix, viewset, basename)

    def get_metadata_view(self, urls):
        metadata = []
        list_name = self.routes[0].name
        for _, viewset, basename in self.registry:
            data_workspace_metadata = viewset.DataWorkspace

            view = viewset()
            view.args = ()
            view.kwargs = {}
            view.format_kwarg = {}
            view.request = None

            metadata.append(
                {
                    "table_name": data_workspace_metadata.table_name,
                    "endpoint": list_name.format(basename=basename),
                    "indexes": getattr(data_workspace_metadata, "indexes", []),
                    "fields": getattr(data_workspace_metadata, "fields", get_fields(view)),
                }
            )

        return TableMetadataView.as_view(metadata=metadata)

    def get_urls(self):
        urls = super().get_urls()

        view = self.get_metadata_view(urls)
        metadata_url = path("table-metadata/", view, name="table-metadata")
        urls.append(metadata_url)

        return urls
