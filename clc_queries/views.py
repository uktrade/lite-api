import json

import reversion
from django.http import JsonResponse
from rest_framework.views import APIView

from clc_queries.libraries.get_clc_query import get_clc_query_by_pk
from clc_queries.serializers import ClcQueryUpdateSerializer
from conf.authentication import GovAuthentication
from static.statuses.libraries.get_case_status import get_case_status_from_status


class ClcQuery(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):
        """
        Update a clc query instance.
        """
        with reversion.create_revision():
            data = json.loads(request.body)
            request.data['status'] = str(get_case_status_from_status(data.get('status')).pk)
            serializer = ClcQueryUpdateSerializer(get_clc_query_by_pk(pk), data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse(data={'clc_query': serializer.data})

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)
