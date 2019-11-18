import json

import reversion
from django.http import JsonResponse, Http404
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from cases.enums import CaseType
from cases.libraries.activity_types import CaseActivityType
from cases.models import CaseActivity
from conf.authentication import ExporterAuthentication, GovAuthentication
from conf.constants import Permissions
from conf.permissions import assert_user_has_permission
from goods.enums import GoodStatus
from goods.serializers import ClcControlGoodSerializer
from goods.libraries.get_goods import get_good
from queries.control_list_classifications.models import ControlListClassificationQuery
from queries.helpers import get_exporter_query
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from organisations.models import UserOrganisationRelationship


class ControlListClassificationsList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def post(self, request):
        """
        Create a new CLC query case instance
        """
        data = JSONParser().parse(request)
        good = get_good(data["good_id"])
        data["organisation"] = request.user.organisation

        # A CLC Query can only be created if the good is in draft status
        if good.status != GoodStatus.DRAFT:
            raise Http404

        good.status = GoodStatus.CLC_QUERY
        good.control_code = data["not_sure_details_control_code"]

        clc_query = ControlListClassificationQuery.objects.create(
            details=data["not_sure_details_details"],
            good=good,
            organisation=data["organisation"],
            type=CaseType.CLC_QUERY,
        )

        good.save()
        clc_query.save()

        return JsonResponse(data={"id": clc_query.id}, status=status.HTTP_201_CREATED)


class ControlListClassificationDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):
        """
        Respond to a control list classification.
        """
        assert_user_has_permission(request.user, Permissions.REVIEW_GOODS)

        query = get_exporter_query(pk)
        data = json.loads(request.body)

        clc_good_serializer = ClcControlGoodSerializer(query.good, data=data)

        with reversion.create_revision():
            if clc_good_serializer.is_valid():
                if "validate_only" not in data or data["validate_only"] == "False":
                    clc_good_serializer.save()
                    query.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
                    query.save()

                    # Add an activity item for the query's case
                    CaseActivity.create(
                        activity_type=CaseActivityType.CLC_RESPONSE, case=query.case.get(), user=request.user,
                    )

                    # Send a notification to the user
                    for user_relationship in UserOrganisationRelationship.objects.filter(
                        organisation=query.organisation
                    ):
                        user_relationship.user.send_notification(query=query)

                    return JsonResponse(data={"control_list_classification_query": clc_good_serializer.data})
                else:
                    return JsonResponse(data={"control_list_classification_query": data}, status=status.HTTP_200_OK,)

            return JsonResponse(data={"errors": clc_good_serializer.errors}, status=status.HTTP_400_BAD_REQUEST,)
