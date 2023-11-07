import copy

from elasticsearch_dsl.query import Q
from django_elasticsearch_dsl_drf.filter_backends.search.query_backends import BaseSearchQueryBackend


class QueryStringQueryBackend(BaseSearchQueryBackend):
    """Query string query backend."""

    query_type = "query_string"

    @classmethod
    def get_query_options(cls, request, view, search_backend):
        query_options = getattr(view, "query_string_options", {})
        return query_options

    @classmethod
    def get_field(cls, field, options):
        if not options:
            options = {}

        field_name = options["field"] if "field" in options else field

        if "boost" in options:
            return "{}^{}".format(field_name, options["boost"])
        return field_name

    @classmethod
    def construct_search(cls, request, view, search_backend):
        """Construct search.

        Note, that multiple searches are not supported (would not raise
        an exception, but would simply take only the first):

            /search/products/?search=sniper AND rifles&search=short AND gun

        In the view-set fields shall be defined in a very simple way. The
        only accepted argument would be boost (per field) for now.
        """
        if hasattr(view, "query_string_search_fields"):
            view_search_fields = copy.copy(
                getattr(view, "query_string_search_fields"),
            )
        else:
            view_search_fields = copy.copy(view.search_fields)

        __is_complex = isinstance(view_search_fields, dict)

        # Getting the list of search query params.
        query_params = search_backend.get_search_query_params(request)

        __queries = []
        for search_term in query_params[:1]:
            __values = search_backend.split_lookup_name(search_term, 1)
            __len_values = len(__values)
            __search_term = search_term

            query_fields = []

            # If we're dealing with case like
            # /search/products/?search=name,report_summary:sniper rifles
            if __len_values > 1:
                _field, value = __values
                __search_term = value
                fields = search_backend.split_lookup_complex_multiple_value(_field)
                for field in fields:
                    if field in view_search_fields:
                        if __is_complex:
                            query_fields.append(
                                cls.get_field(field, view_search_fields[field]),
                            )
                        else:
                            query_fields.append(field)

            # If it's just a simple search like
            # /search/products/?search=sniper AND rifles
            # Fields shall be defined in a very simple way.
            else:
                # If it is defined as dict
                if __is_complex:
                    for field, options in view_search_fields.items():
                        query_fields.append(cls.get_field(field, options))

                # just as a list
                else:
                    query_fields = copy.copy(view_search_fields)

            __queries.append(
                Q(
                    cls.query_type,
                    query=__search_term,
                    fields=query_fields,
                    **cls.get_query_options(request, view, search_backend),
                )
            )

        return __queries
