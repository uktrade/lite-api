from django.db import transaction
from django.db.models import Value
from django.db.models.functions import Concat
from django.http.response import JsonResponse, HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases import service
from cases.helpers import create_grouped_advice
from cases.libraries.get_case import get_case, get_case_document
from cases.libraries.get_destination import get_destination
from cases.libraries.get_ecju_queries import get_ecju_query
from cases.libraries.delete_notifications import delete_exporter_notifications
from cases.libraries.post_advice import (
    post_advice,
    check_if_final_advice_exists,
    check_if_team_advice_exists,
    check_if_user_cannot_manage_team_advice,
    case_advice_contains_refusal,
)
from cases.models import CaseDocument, EcjuQuery, Advice, TeamAdvice, FinalAdvice, GoodCountryDecision
from cases.serializers import (
    CaseDocumentViewSerializer,
    CaseDocumentCreateSerializer,
    EcjuQueryCreateSerializer,
    CaseDetailSerializer,
    CaseAdviceSerializer,
    EcjuQueryGovSerializer,
    EcjuQueryExporterSerializer,
    CaseTeamAdviceSerializer,
    CaseFinalAdviceSerializer,
    GoodCountryDecisionSerializer,
    CaseOfficerUpdateSerializer,
)
from conf import constants
from conf.authentication import GovAuthentication, SharedAuthentication
from conf.permissions import assert_user_has_permission
from documents.libraries.delete_documents_on_bad_request import delete_documents_on_bad_request
from goodstype.helpers import get_goods_type
from parties.serializers import PartyWithFlagsSerializer
from static.countries.helpers import get_country
from static.countries.models import Country
from static.countries.serializers import CountryWithFlagsSerializer
from users.enums import UserStatuses
from users.libraries.get_user import get_user_by_pk
from users.models import ExporterUser, GovUser
from users.serializers import CaseOfficerUserDisplaySerializer


class CaseDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        """
        Retrieve a case instance
        """
        case = get_case(pk)
        serializer = CaseDetailSerializer(case, context=request, team=request.user.team)

        return JsonResponse(data={"case": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={400: 'Input error, "queues" should be an array with at least one existing queue'})
    @transaction.atomic
    def put(self, request, pk):
        """
        Change the queues a case belongs to
        """
        case = get_case(pk)
        serializer = CaseDetailSerializer(case, data=request.data, team=request.user.team, partial=True)
        if serializer.is_valid():
            service.update_case_queues(user=request.user, case=case, queues=serializer.validated_data["queues"])
            serializer.save()

            return JsonResponse(data={"case": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CaseDocuments(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Returns a list of documents on the specified case
        """
        case = get_case(pk)
        case_documents = CaseDocument.objects.filter(case=case).order_by("-created_at")
        serializer = CaseDocumentViewSerializer(case_documents, many=True)

        return JsonResponse(data={"documents": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CaseDocumentCreateSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    def post(self, request, pk):
        """
        Adds a document to the specified case
        """
        case = get_case(pk)
        case_id = str(case.id)
        data = request.data

        for document in data:
            document["case"] = case_id
            document["user"] = request.user.id

        serializer = CaseDocumentCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()

            for document in serializer.data:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UPLOAD_CASE_DOCUMENT,
                    target=case,
                    payload={"file_name": document["name"]},
                )

            return JsonResponse(data={"documents": serializer.data}, status=status.HTTP_201_CREATED)

        delete_documents_on_bad_request(data)
        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CaseDocumentDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk, s3_key):
        """
        Returns a list of documents on the specified case
        """
        case = get_case(pk)
        case_document = get_case_document(case, s3_key)
        serializer = CaseDocumentViewSerializer(case_document)
        return JsonResponse(data={"document": serializer.data}, status=status.HTTP_200_OK)


class CaseAdvice(APIView):
    authentication_classes = (GovAuthentication,)

    case = None
    advice = None
    serializer_object = None

    def dispatch(self, request, *args, **kwargs):
        self.case = get_case(kwargs["pk"])
        # We exclude any team of final level advice objects
        self.advice = (
            Advice.objects.filter(case=self.case).exclude(teamadvice__isnull=False).exclude(finaladvice__isnull=False)
        )
        self.serializer_object = CaseAdviceSerializer

        return super(CaseAdvice, self).dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        """
        Returns all advice for a case
        """
        serializer = self.serializer_object(self.advice, many=True)
        return JsonResponse(data={"advice": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CaseAdviceSerializer, responses={400: "JSON parse error"})
    def post(self, request, pk):
        """
        Creates advice for a case
        """
        final_advice_exists = check_if_final_advice_exists(self.case)
        team_advice_exists = check_if_team_advice_exists(self.case, self.request.user)
        if final_advice_exists:
            return final_advice_exists
        elif team_advice_exists:
            return team_advice_exists
        else:
            return post_advice(request, self.case, self.serializer_object, team=False)


class ViewTeamAdvice(APIView):
    def get(self, request, pk, team_pk):
        team_advice = TeamAdvice.objects.filter(case__pk=pk, team__pk=team_pk)

        serializer = CaseTeamAdviceSerializer(team_advice, many=True)
        return JsonResponse(data={"advice": serializer.data}, status=status.HTTP_200_OK)


class CaseTeamAdvice(APIView):
    authentication_classes = (GovAuthentication,)

    case = None
    advice = None
    team_advice = None
    serializer_object = None

    def dispatch(self, request, *args, **kwargs):
        self.case = get_case(kwargs["pk"])
        self.advice = Advice.objects.filter(case=self.case)
        self.team_advice = TeamAdvice.objects.filter(case=self.case).order_by("created_at")
        self.serializer_object = CaseTeamAdviceSerializer

        return super(CaseTeamAdvice, self).dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        """
        Concatenates all advice for a case and returns it or just returns if team advice already exists
        """

        if self.team_advice.filter(team=request.user.team).count() == 0:
            user_cannot_manage_team_advice = check_if_user_cannot_manage_team_advice(pk, request.user)
            if user_cannot_manage_team_advice:
                return user_cannot_manage_team_advice

            team = self.request.user.team
            advice = self.advice.filter(user__team=team)
            create_grouped_advice(self.case, self.request, advice, TeamAdvice)
            case_advice_contains_refusal(pk)

            audit_trail_service.create(
                actor=request.user, verb=AuditType.CREATED_TEAM_ADVICE, target=self.case,
            )
            team_advice = TeamAdvice.objects.filter(case=self.case, team=team).order_by("created_at")
        else:
            team_advice = self.team_advice
        serializer = self.serializer_object(team_advice, many=True)
        return JsonResponse(data={"advice": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CaseTeamAdviceSerializer, responses={400: "JSON parse error"})
    def post(self, request, pk):
        """
        Creates advice for a case
        """
        user_cannot_manage_team_advice = check_if_user_cannot_manage_team_advice(pk, request.user)
        if user_cannot_manage_team_advice:
            return user_cannot_manage_team_advice

        final_advice_exists = check_if_final_advice_exists(self.case)
        if final_advice_exists:
            return final_advice_exists

        advice = post_advice(request, self.case, self.serializer_object, team=True)
        case_advice_contains_refusal(pk)
        return advice

    def delete(self, request, pk):
        """
        Clears team level advice and reopens the advice for user level for that team
        """
        user_cannot_manage_team_advice = check_if_user_cannot_manage_team_advice(pk, request.user)
        if user_cannot_manage_team_advice:
            return user_cannot_manage_team_advice

        self.team_advice.filter(team=self.request.user.team).delete()
        case_advice_contains_refusal(pk)
        audit_trail_service.create(actor=request.user, verb=AuditType.CLEARED_TEAM_ADVICE, target=self.case)
        return JsonResponse(data={"status": "success"}, status=status.HTTP_200_OK)


class ViewFinalAdvice(APIView):
    def get(self, request, pk):
        case = get_case(pk)
        final_advice = FinalAdvice.objects.filter(case=case)

        serializer = CaseFinalAdviceSerializer(final_advice, many=True)
        return JsonResponse(data={"advice": serializer.data}, status=status.HTTP_200_OK)


class CaseFinalAdvice(APIView):
    authentication_classes = (GovAuthentication,)

    case = None
    team_advice = None
    final_advice = None
    serializer_object = None

    def dispatch(self, request, *args, **kwargs):
        self.case = get_case(kwargs["pk"])
        self.team_advice = TeamAdvice.objects.filter(case=self.case)
        self.final_advice = FinalAdvice.objects.filter(case=self.case).order_by("created_at")
        self.serializer_object = CaseFinalAdviceSerializer

        return super(CaseFinalAdvice, self).dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        """
        Concatenates all advice for a case and returns it or just returns if team advice already exists
        """
        if len(self.final_advice) == 0:
            assert_user_has_permission(request.user, constants.GovPermissions.MANAGE_FINAL_ADVICE)
            # We pass in the class of advice we are creating
            create_grouped_advice(self.case, self.request, self.team_advice, FinalAdvice)

            audit_trail_service.create(
                actor=request.user, verb=AuditType.CREATED_FINAL_ADVICE, target=self.case,
            )
            final_advice = FinalAdvice.objects.filter(case=self.case).order_by("created_at")
        else:
            final_advice = self.final_advice

        serializer = self.serializer_object(final_advice, many=True)
        return JsonResponse(data={"advice": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CaseFinalAdviceSerializer, responses={400: "JSON parse error"})
    def post(self, request, pk):
        """
        Creates advice for a case
        """
        assert_user_has_permission(request.user, constants.GovPermissions.MANAGE_FINAL_ADVICE)
        return post_advice(request, self.case, self.serializer_object, team=True)

    def delete(self, request, pk):
        """
        Clears team level advice and reopens the advice for user level for that team
        """
        assert_user_has_permission(request.user, constants.GovPermissions.MANAGE_FINAL_ADVICE)
        self.final_advice.delete()
        audit_trail_service.create(
            actor=request.user, verb=AuditType.CLEARED_FINAL_ADVICE, target=self.case,
        )
        return JsonResponse(data={"status": "success"}, status=status.HTTP_200_OK)


class CaseEcjuQueries(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        """
        Returns the list of ECJU Queries on a case
        """
        case = get_case(pk)
        case_ecju_queries = EcjuQuery.objects.filter(case=case).order_by("created_at")

        if isinstance(request.user, ExporterUser):
            serializer = EcjuQueryExporterSerializer(case_ecju_queries, many=True)
            delete_exporter_notifications(
                user=request.user, organisation=request.user.organisation, objects=case_ecju_queries
            )
        else:
            serializer = EcjuQueryGovSerializer(case_ecju_queries, many=True)

        return JsonResponse(data={"ecju_queries": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        """
        Add a new ECJU query
        """
        data = JSONParser().parse(request)
        data["case"] = pk
        data["raised_by_user"] = request.user.id
        serializer = EcjuQueryCreateSerializer(data=data)

        if serializer.is_valid():
            if "validate_only" not in data or not data["validate_only"]:
                serializer.save()

                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ECJU_QUERY,
                    action_object=serializer.instance,
                    target=serializer.instance.case,
                    payload={"ecju_query": data["question"]},
                )

                return JsonResponse(data={"ecju_query_id": serializer.data["id"]}, status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data={}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EcjuQueryDetail(APIView):
    """
    Details of a specific ECJU query
    """

    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk, ecju_pk):
        """
        Returns details of an ecju query
        """
        ecju_query = get_ecju_query(ecju_pk)
        serializer = EcjuQueryExporterSerializer(ecju_query)
        return JsonResponse(data={"ecju_query": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, pk, ecju_pk):
        """
        If not validate only Will update the ecju query instance, with a response, and return the data details.
        If validate only, this will return if the data is acceptable or not.
        """
        ecju_query = get_ecju_query(ecju_pk)

        data = {"response": request.data["response"], "responded_by_user": str(request.user.id)}

        serializer = EcjuQueryExporterSerializer(instance=ecju_query, data=data, partial=True)

        if serializer.is_valid():
            if "validate_only" not in request.data or not request.data["validate_only"]:
                serializer.save()

                return JsonResponse(data={"ecju_query": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data={}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class GoodsCountriesDecisions(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        assert_user_has_permission(request.user, constants.GovPermissions.MANAGE_FINAL_ADVICE)
        goods_countries = GoodCountryDecision.objects.filter(case=pk)
        serializer = GoodCountryDecisionSerializer(goods_countries, many=True)

        return JsonResponse(data={"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        assert_user_has_permission(request.user, constants.GovPermissions.MANAGE_FINAL_ADVICE)
        data = JSONParser().parse(request).get("good_countries")

        serializer = GoodCountryDecisionSerializer(data=data, many=True)
        if serializer.is_valid():
            for item in data:
                GoodCountryDecision(
                    good=get_goods_type(item["good"]),
                    case=get_case(item["case"]),
                    country=get_country(item["country"]),
                    decision=item["decision"],
                ).save()

            return JsonResponse(data={"data": data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class Destination(APIView):
    def get(self, request, pk):
        destination = get_destination(pk)

        if isinstance(destination, Country):
            serializer = CountryWithFlagsSerializer(destination)
        else:
            serializer = PartyWithFlagsSerializer(destination)

        return JsonResponse(data={"destination": serializer.data}, status=status.HTTP_200_OK)


class CaseOfficer(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def post(self, request, pk, gov_user_pk):
        """
        Assigns a gov user to be the case officer for a case
        """
        case = get_case(pk)
        data = {"case_officer": gov_user_pk}

        serializer = CaseOfficerUpdateSerializer(instance=case, data=data)

        if serializer.is_valid():
            user = get_user_by_pk(gov_user_pk)

            serializer.save()
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.ADD_CASE_OFFICER_TO_CASE,
                target=case,
                payload={"case_officer": user.email if not user.first_name else f"{user.first_name} {user.last_name}"},
            )

            return HttpResponse(status=status.HTTP_204_NO_CONTENT)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CaseOfficers(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Gets the current case officer for a case, and gets a list of gov users based on the
        search_term(name of user) passed in
        """
        data = {}
        case_officer = get_case(pk).case_officer
        name = request.GET.get("search_term", "")
        if case_officer:
            data["case_officer"] = CaseOfficerUserDisplaySerializer(case_officer).data
        else:
            data["case_officer"] = None
        data["users"] = CaseOfficerUserDisplaySerializer(
            GovUser.objects.exclude(status=UserStatuses.DEACTIVATED)
            .annotate(full_name=Concat("first_name", Value(" "), "last_name"))
            .filter(full_name__icontains=name),
            many=True,
        ).data

        return JsonResponse(data={"GovUsers": data}, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, pk):
        """
        Removes the case officer currently assigned to a case off of it.
        """
        case = get_case(pk)
        if not case.case_officer:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        data = {"case_officer": None}

        serializer = CaseOfficerUpdateSerializer(instance=case, data=data)

        if serializer.is_valid():
            user = case.case_officer

            serializer.save()
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.REMOVE_CASE_OFFICER_FROM_CASE,
                target=case,
                payload={"case_officer": user.email if not user.first_name else f"{user.first_name} {user.last_name}"},
            )

            return HttpResponse(status=status.HTTP_204_NO_CONTENT)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
