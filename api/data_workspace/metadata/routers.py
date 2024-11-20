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


class TableMetadataRouter(DefaultRouter):
    def register(self, viewset):
        prefix = viewset.DataWorkspace.table_name.replace("_", "-")
        basename = f"dw-{prefix}"

        super().register(prefix, viewset, basename)

    def get_metadata_view(self, urls):
        metadata = []
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            data_workspace_metadata = viewset.DataWorkspace
            metadata.append(
                {
                    "table_name": data_workspace_metadata.table_name,
                    "endpoint": list_name.format(basename=basename),
                    "indexes": getattr(data_workspace_metadata, "indexes", []),
                    "fields": getattr(data_workspace_metadata, "fields", []),
                }
            )

        return TableMetadataView.as_view(metadata=metadata)

    def get_urls(self):
        urls = super().get_urls()

        view = self.get_metadata_view(urls)
        metadata_url = path("table-metadata/", view, name="table-metadata")
        urls.append(metadata_url)

        return urls
