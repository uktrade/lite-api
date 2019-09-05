import json

import reversion
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from cases.enums import CaseType
from cases.models import Case
from conf.authentication import GovAuthentication
from goods.enums import GoodStatus
from goods.libraries.get_good import get_good
from queries.control_list_classifications.models import ControlListClassificationQuery
from queries.control_list_classifications.serializers import ClcQueryUpdateSerializer
from queries.helpers import get_exporter_query
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status


class ControlListClassificationsList(APIView):
    def post(self, request):
        """
        Create a new CLC query case instance
        """
        data = JSONParser().parse(request)
        good = get_good(data['good_id'])

        good.status = GoodStatus.SUBMITTED
        if data['not_sure_details_control_code'] == '':
            return JsonResponse(data={'errors': {
                'not_sure_details_control_code': [ErrorDetail('This field may not be blank.', code='blank')]
            }}, status=status.HTTP_400_BAD_REQUEST)

        good.control_code = data['not_sure_details_control_code']
        good.save()

        clc_query = ControlListClassificationQuery(details=data['not_sure_details_details'],
                                                   good=good,
                                                   status=get_case_status_from_status(CaseStatusEnum.SUBMITTED))
        clc_query.save()

        return JsonResponse(data={'id': clc_query.id}, status=status.HTTP_201_CREATED)


class ControlListClassificationDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):
        """
        Update a clc query instance.
        """
        with reversion.create_revision():
            data = json.loads(request.body)
            data['status'] = str(get_case_status_from_status(data.get('status')).pk)
            serializer = ClcQueryUpdateSerializer(get_exporter_query(pk), data=data, partial=True)

            if serializer.is_valid():
                with reversion.create_revision():
                    reversion.set_comment('Updated CLC Query Details')
                    reversion.set_user(request.user)
                    serializer.save()
                return JsonResponse(data={'clc_query': serializer.data})

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)
