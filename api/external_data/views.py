from elasticsearch_dsl import Search, Q
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from django_elasticsearch_dsl_drf import filter_backends
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet

from django.conf import settings

from api.core.authentication import GovAuthentication
from api.conf.pagination import MaxPageNumberPagination
from api.external_data import documents, models, serializers


class DenialViewSet(viewsets.ModelViewSet):
    queryset = models.DenialEntity.objects.all()
    authentication_classes = (GovAuthentication,)

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.DenialFromCSVFileSerializer
        return serializers.DenialEntitySerializer

    def perform_create(self, serializer):
        pass


class SanctionViewSet(viewsets.ModelViewSet):
    authentication_classes = (GovAuthentication,)
    serializer_class = serializers.SanctionMatchSerializer
    queryset = models.SanctionMatch.objects.all()

    def perform_create(self, serializer):
        pass


class ElasticApiView(APIView):
    authentication_classes = (GovAuthentication,)
    elastic_index = settings.ELASTICSEARCH_DENIALS_INDEX_ALIAS
    search_keys = []

    def parse_search(self, search_parameters):
        search_dict = {"country": search_parameters.get("country", ""), "page": search_parameters.get("page", "")}
        search_params = search_parameters.getlist("search")
        for item in search_params:
            key, value = item.split(":")
            if search_dict.get(key):
                search_dict[key].append(value)
            else:
                self.search_keys.append(key)
                search_dict[key] = [value]
        return search_dict

    def get_pagination(self, page):
        results_per_page = settings.STREAM_PAGE_SIZE
        end = results_per_page * int(page)
        start = end - results_per_page
        return start, end

    def get_query(self, params, search_keys):
        search_value = []
        for key in search_keys:
            if params.get(key):
                for values in params[key]:
                    search_value.append({"match": {key: {"query": values}}})

        return Q(
            "bool",
            filter=[
                Q("term", is_revoked=False),
                Q("bool", must_not=Q("term", notifying_government="United Kingdom")),
                {"terms": {"country.raw": [params["country"]]}},
            ],
            should=search_value,
            minimum_should_match=1,
        )

    def results_json_parseable(self, results):
        return [result.to_dict() for result in results]

    def get(self, request):
        search_params = self.parse_search(request.GET)
        start, end = self.get_pagination(search_params["page"])
        search = Search(index=self.elastic_index)
        query = self.get_query(search_params, self.search_keys)
        results = search.query(query).execute()
        final_results = self.results_json_parseable(results[start:end])

        response = {
            "results": final_results,
            "total_pages": len(results) / settings.STREAM_PAGE_SIZE,
            "count": len(final_results),
        }
        return Response(response)


class DenialSearchView(ElasticApiView):
    elastic_index = settings.ELASTICSEARCH_DENIALS_INDEX_ALIAS


class SanctionSearchView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        search = Search(index=settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS)
        results = search.query("match", name=request.GET["name"]).execute()
        return Response(results)
