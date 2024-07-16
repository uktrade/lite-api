from . import filter_backends
from rest_framework.exceptions import ValidationError


class QueryStringValidationMixin:
    """
    Query String validation mixin is used to verify if query string
    passed in from a client is well formed prior to executing against ES.
    """

    def validate_search_terms(self):
        query_params = self.request.GET.copy()
        search_term = query_params.get("search")

        # This is required as query_string is unable to handle a single /
        search_term = search_term.replace("/", "//")

        # Validation is only required if we are using QueryStringSearchFilterBackend

        if filter_backends.QueryStringSearchFilterBackend not in self.filter_backends:
            return True

        # create a query with the given query params
        query = {
            "query": {
                "query_string": {
                    "fields": ["*"],
                    "query": f"{search_term}",
                }
            }
        }

        response = self.document._index.validate_query(body=query)
        return response["valid"]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not self.validate_search_terms():
            raise ValidationError({"search": "Invalid search string"})
