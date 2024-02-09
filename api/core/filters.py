from rest_framework import filters

from django.core.exceptions import ImproperlyConfigured


class ParentFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        parent_id_lookup_field = getattr(view, "parent_id_lookup_field", None)
        if not parent_id_lookup_field:
            raise ImproperlyConfigured(
                f"Cannot use {self.__class__.__name__} on a view which does not have a parent_id_lookup_field attribute"
            )

        lookup = {
            parent_id_lookup_field: view.kwargs["pk"],
        }
        return queryset.filter(**lookup)
