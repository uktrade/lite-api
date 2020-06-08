from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http.response import JsonResponse, HttpResponse, Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.models import CountryOnApplication
from applications.serializers.advice import CountryWithFlagsSerializer
from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from cases.enums import CaseTypeSubTypeEnum, AdviceType, AdviceLevel, ECJUQueryType
from cases.generated_documents.models import GeneratedCaseDocument
from cases.generated_documents.serializers import AdviceDocumentGovSerializer
from cases.libraries.advice import group_advice
from cases.libraries.delete_notifications import delete_exporter_notifications
from cases.libraries.get_case import get_case, get_case_document
from cases.libraries.get_destination import get_destination
from cases.libraries.get_ecju_queries import get_ecju_query
from cases.libraries.post_advice import (
    post_advice,
    check_if_final_advice_exists,
    check_if_team_advice_exists,
    check_if_user_cannot_manage_team_advice,
    case_advice_contains_refusal,
)
from cases.models import CaseDocument, EcjuQuery, Advice, GoodCountryDecision, CaseAssignment, Case
from cases.serializers import (
    CaseDocumentViewSerializer,
    CaseDocumentCreateSerializer,
    EcjuQueryCreateSerializer,
    CaseDetailSerializer,
    EcjuQueryGovSerializer,
    EcjuQueryExporterSerializer,
    CaseAdviceSerializer,
    GoodCountryDecisionSerializer,
    CaseOfficerUpdateSerializer,
)
from conf import constants
from conf.authentication import GovAuthentication, SharedAuthentication, ExporterAuthentication
from conf.constants import GovPermissions
from conf.exceptions import NotFoundError, BadRequestError
from conf.permissions import assert_user_has_permission
from documents.libraries.delete_documents_on_bad_request import delete_documents_on_bad_request
from documents.libraries.s3_operations import document_download_stream
from documents.models import Document
from goodstype.helpers import get_goods_type
from gov_notify import service as gov_notify_service
from gov_notify.enums import TemplateType
from gov_notify.payloads import EcjuCreatedEmailData, ApplicationStatusEmailData
from licences.models import Licence
from licences.serializers.create_licence import LicenceCreateSerializer
from lite_content.lite_api.strings import Documents, Cases
from organisations.libraries.get_organisation import get_request_user_organisation_id
from parties.models import Party
from parties.serializers import PartySerializer, AdditionalContactSerializer
from queues.models import Queue
from queues.serializers import TinyQueueSerializer
from static.countries.helpers import get_country
from static.countries.models import Country
from static.decisions.models import Decision
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.libraries.get_user import get_user_by_pk
from users.models import ExporterUser
from workflow.automation import run_routing_rules
from workflow.user_queue_assignment import user_queue_assignment_workflow


class CaseDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieve a case instance
        """
        case = get_case(pk)
        serializer = CaseDetailSerializer(case, user=request.user, team=request.user.team)

        return JsonResponse(data={"case": serializer.data}, status=status.HTTP_200_OK)


class SetQueues(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        case = get_case(pk)
        request_queues = set(request.data.get("queues", []))
        queues = Queue.objects.filter(id__in=request_queues)

        if len(request_queues) > len(queues):
            queues_not_found = list(request_queues - set(str(id) for id in queues.values_list("id", flat=True)))
            return JsonResponse(
                data={"errors": {"queues": [Cases.Queue.NOT_FOUND + str(queues_not_found)]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        initial_queues = set(case.queues.all())
        queues = set(queues)
        case.queues.set(request_queues)

        removed_queues = initial_queues - queues
        new_queues = queues - initial_queues
        if removed_queues:
            # Remove case assignments when the case is remove from the queue
            CaseAssignment.objects.filter(case=case, queue__in=removed_queues).delete()
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.REMOVE_CASE,
                target=case,
                payload={"queues": sorted([queue.name for queue in removed_queues])},
            )
        if new_queues:
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.MOVE_CASE,
                target=case,
                payload={"queues": sorted([queue.name for queue in new_queues])},
            )
        return JsonResponse(data={"queues": list(request_queues)}, status=status.HTTP_200_OK)


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
        data = request.data

        for document in data:
            document["case"] = pk
            document["user"] = request.user.id
            document["visible_to_exporter"] = True

        serializer = CaseDocumentCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()

            for document in serializer.data:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UPLOAD_CASE_DOCUMENT,
                    target=get_case(pk),
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


class ExporterCaseDocumentDownload(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, case_pk, document_pk):
        case = get_case(case_pk)
        if case.organisation.id != get_request_user_organisation_id(request):
            return HttpResponse(status.HTTP_401_UNAUTHORIZED)
        try:
            document = CaseDocument.objects.get(id=document_pk, case=case)
            return document_download_stream(document)
        except Document.DoesNotExist:
            raise NotFoundError({"document": Documents.DOCUMENT_NOT_FOUND})


class UserAdvice(APIView):
    authentication_classes = (GovAuthentication,)

    case = None
    advice = None

    def dispatch(self, request, *args, **kwargs):
        self.case = get_case(kwargs["pk"])
        self.advice = Advice.objects.get_user_advice(self.case)

        return super(UserAdvice, self).dispatch(request, *args, **kwargs)

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
            return post_advice(request, self.case, AdviceLevel.USER)


class TeamAdviceView(APIView):
    authentication_classes = (GovAuthentication,)

    case = None
    advice = None
    team_advice = None

    def dispatch(self, request, *args, **kwargs):
        self.case = get_case(kwargs["pk"])
        self.advice = Advice.objects.filter(case=self.case)
        self.team_advice = Advice.objects.get_team_advice(self.case)

        return super(TeamAdviceView, self).dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        """
        Concatenates all advice for a case
        """
        if self.team_advice.filter(team=request.user.team).count() == 0:
            user_cannot_manage_team_advice = check_if_user_cannot_manage_team_advice(pk, request.user)
            if user_cannot_manage_team_advice:
                return user_cannot_manage_team_advice

            team = self.request.user.team_id
            advice = self.advice.filter(user__team_id=team)
            group_advice(self.case, advice, request.user, AdviceLevel.TEAM)
            case_advice_contains_refusal(pk)

            audit_trail_service.create(
                actor=request.user, verb=AuditType.CREATED_TEAM_ADVICE, target=self.case,
            )

            team_advice = Advice.objects.filter(case=self.case, team_id=team).order_by("-created_at")
        else:
            team_advice = self.team_advice

        serializer = CaseAdviceSerializer(team_advice, many=True)
        return JsonResponse(data={"advice": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CaseAdviceSerializer, responses={400: "JSON parse error"})
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

        advice = post_advice(request, self.case, AdviceLevel.TEAM, team=True)
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


class FinalAdviceDocuments(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Gets all advice types and any documents generated for those types of advice.
        """
        # Get all advice
        advice_values = AdviceType.as_dict()
        final_advice = Advice.objects.filter(case__id=pk).distinct("type").values_list("type", flat=True)
        advice_documents = {advice_type: {"value": advice_values[advice_type]} for advice_type in final_advice}

        # Add advice documents
        generated_advice_documents = GeneratedCaseDocument.objects.filter(advice_type__in=final_advice, case__id=pk)
        generated_advice_documents = AdviceDocumentGovSerializer(generated_advice_documents, many=True,).data
        for document in generated_advice_documents:
            advice_type = document["advice_type"]["key"]
            advice_documents[advice_type]["document"] = document

        return JsonResponse(data={"documents": advice_documents}, status=status.HTTP_200_OK)


class FinalAdvice(APIView):
    authentication_classes = (GovAuthentication,)

    case = None
    team_advice = None
    final_advice = None

    def dispatch(self, request, *args, **kwargs):
        self.case = get_case(kwargs["pk"])
        self.team_advice = Advice.objects.get_team_advice(case=self.case)
        self.final_advice = Advice.objects.get_final_advice(case=self.case).order_by("created_at")

        return super(FinalAdvice, self).dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        """
        Concatenates all advice for a case and returns it or just returns if final advice already exists
        """
        if len(self.final_advice) == 0:
            assert_user_has_permission(request.user, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)

            group_advice(self.case, self.team_advice, request.user, AdviceLevel.FINAL)

            audit_trail_service.create(
                actor=request.user, verb=AuditType.CREATED_FINAL_ADVICE, target=self.case,
            )
            final_advice = Advice.objects.filter(case=self.case).order_by("-created_at")
        else:
            final_advice = self.final_advice

        serializer = CaseAdviceSerializer(final_advice, many=True)
        return JsonResponse(data={"advice": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CaseAdviceSerializer, responses={400: "JSON parse error"})
    def post(self, request, pk):
        """
        Creates advice for a case
        """
        assert_user_has_permission(request.user, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)
        return post_advice(request, self.case, AdviceLevel.FINAL, team=True)

    def delete(self, request, pk):
        """
        Clears team level advice and reopens the advice for user level for that team
        """
        assert_user_has_permission(request.user, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)
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
                user=request.user, organisation_id=get_request_user_organisation_id(request), objects=case_ecju_queries
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
        data["team"] = request.user.team.id
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
                if serializer.data["query_type"]["key"] == ECJUQueryType.ECJU:
                    # Only send email for standard ECJU queries
                    application_info = (
                        Case.objects.annotate(email=F("submitted_by__email"), name=F("baseapplication__name"))
                        .values("email", "name", "reference_code")
                        .get(id=pk)
                    )
                    gov_notify_service.send_email(
                        email_address=application_info["email"],
                        template_type=TemplateType.ECJU_CREATED,
                        data=EcjuCreatedEmailData(
                            application_reference=application_info["reference_code"],
                            ecju_reference=application_info["name"],
                            link=f"{settings.EXPORTER_BASE_URL}/applications/{pk}/ecju-queries/",
                        ),
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
        assert_user_has_permission(request.user, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)
        goods_countries = GoodCountryDecision.objects.filter(case=pk)
        serializer = GoodCountryDecisionSerializer(goods_countries, many=True)

        return JsonResponse(data={"data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        assert_user_has_permission(request.user, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)
        data = request.data.get("good_countries")

        if not data:
            raise BadRequestError({"good_countries": ["Select a decision for each good and country"]})

        country_count = CountryOnApplication.objects.filter(application=get_case(data[0]["case"])).count()

        if len(data) != country_count:
            raise BadRequestError({"good_countries": ["Select a decision for each good and country"]})

        serializer = GoodCountryDecisionSerializer(data=data, many=True)

        if serializer.is_valid(raise_exception=True):
            for item in data:
                GoodCountryDecision(
                    good=get_goods_type(item["good"]),
                    case=get_case(item["case"]),
                    country=get_country(item["country"]),
                    decision=item["decision"],
                ).save()

            return JsonResponse(data={"data": data}, status=status.HTTP_200_OK)


class Destination(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        destination = get_destination(pk)

        if isinstance(destination, Country):
            serializer = CountryWithFlagsSerializer(destination)
        else:
            serializer = PartySerializer(destination)

        return JsonResponse(data={"destination": serializer.data}, status=status.HTTP_200_OK)


class CaseOfficer(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        """
        Assigns a gov user to be the case officer for a case
        """
        case = get_case(pk)
        gov_user_pk = request.data.get("gov_user_pk")

        if not gov_user_pk:
            return JsonResponse(
                data={"errors": {"user": [Cases.CaseOfficerPage.NONE]}}, status=status.HTTP_400_BAD_REQUEST
            )

        data = {"case_officer": gov_user_pk}
        serializer = CaseOfficerUpdateSerializer(instance=case, data=data)

        if serializer.is_valid(raise_exception=True):
            user = get_user_by_pk(gov_user_pk)
            serializer.save()

            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.ADD_CASE_OFFICER_TO_CASE,
                target=case,
                payload={"case_officer": user.email if not user.first_name else f"{user.first_name} {user.last_name}"},
            )

            return JsonResponse(data={}, status=status.HTTP_200_OK)

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

        if serializer.is_valid(raise_exception=True):
            user = case.case_officer

            serializer.save()
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.REMOVE_CASE_OFFICER_FROM_CASE,
                target=case,
                payload={"case_officer": user.email if not user.first_name else f"{user.first_name} {user.last_name}"},
            )

            return JsonResponse(data={}, status=status.HTTP_200_OK)


class FinaliseView(RetrieveUpdateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = LicenceCreateSerializer

    def get_object(self):
        # Due to a bug where multiple licences were being created, we get the latest one.
        licence = Licence.objects.filter(application=self.kwargs["pk"]).order_by("created_at").last()
        if not licence:
            raise Http404(Licence.DoesNotExist)

    @transaction.atomic
    def put(self, request, pk):
        """
        Finalise & grant a Licence
        """
        case = get_case(pk)

        # Check Permissions
        if CaseTypeSubTypeEnum.is_mod_clearance(case.case_type.sub_type):
            assert_user_has_permission(request.user, GovPermissions.MANAGE_CLEARANCE_FINAL_ADVICE)
        else:
            assert_user_has_permission(request.user, GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)

        # Check all decision types have documents
        required_decisions = set(Advice.objects.filter(case=case).distinct("type").values_list("type", flat=True))
        generated_document_decisions = set(
            GeneratedCaseDocument.objects.filter(advice_type__isnull=False, case=case).values_list(
                "advice_type", flat=True
            )
        )
        if not required_decisions.issubset(generated_document_decisions):
            return JsonResponse(data={"errors": [Cases.Licence.MISSING_DOCUMENTS]}, status=status.HTTP_400_BAD_REQUEST,)

        return_payload = {"case": pk}

        # Finalise Case
        old_status = case.status.status
        case.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        case.save()

        gov_notify_service.send_email(
            email_address=case.submitted_by.email,
            template_type=TemplateType.APPLICATION_STATUS,
            data=ApplicationStatusEmailData(
                application_reference=case.baseapplication.name,
                case_reference=case.reference_code,
                link=f"{settings.EXPORTER_BASE_URL}/applications/{pk}",
            ),
        )

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.UPDATED_STATUS,
            target=case,
            payload={"status": {"new": case.status.status, "old": old_status}},
        )

        # If a licence object exists, finalise the licence.
        # Due to a bug where multiple licences were being created, we get the latest one.
        licence = Licence.objects.filter(application=case).order_by("created_at").last()
        if licence:
            licence.is_complete = True
            licence.decisions.set([Decision.objects.get(name=decision) for decision in required_decisions])
            licence.save()
            return_payload["licence"] = licence.id
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.GRANTED_APPLICATION,
                target=case,
                payload={"licence_duration": licence.duration, "start_date": licence.start_date.strftime("%Y-%m-%d")},
            )

        # Show documents to exporter & notify
        documents = GeneratedCaseDocument.objects.filter(advice_type__isnull=False, case=case)
        documents.update(visible_to_exporter=True)
        for document in documents:
            document.send_exporter_notifications()

        return JsonResponse(return_payload, status=status.HTTP_201_CREATED)


class AssignedQueues(APIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = TinyQueueSerializer

    def get(self, request, pk):
        # Get all queues where this user is assigned to this case
        queues = Queue.objects.filter(case_assignments__user=request.user.pk, case_assignments__case=pk)
        serializer = TinyQueueSerializer(queues, many=True)
        return JsonResponse(data={"queues": serializer.data}, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, pk):
        queues = request.data.get("queues")
        if queues:
            queue_names = []
            assignments = (
                CaseAssignment.objects.select_related("queue")
                .filter(user=request.user, case__id=pk, queue__id__in=queues)
                .order_by("queue__name")
            )
            case = get_case(pk)

            if assignments:
                queues = [assignment.queue for assignment in assignments]
                queue_names = [queue.name for queue in queues]
                assignments.delete()
                user_queue_assignment_workflow(queues, case)
                audit_trail_service.create(
                    actor=request.user, verb=AuditType.UNASSIGNED_QUEUES, target=case, payload={"queues": queue_names},
                )
            else:
                # When users click done without queue assignments
                # Only a single queue ID can be passed
                if len(queues) != 1:
                    return JsonResponse(
                        data={"errors": {"queues": [Cases.UnassignQueues.NOT_ASSIGNED_MULTIPLE_QUEUES]}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # Check queue belongs to that users team
                queues = Queue.objects.filter(id=queues[0], team=request.user.team)
                if not queues.exists():
                    return JsonResponse(
                        data={"errors": {"queues": [Cases.UnassignQueues.INVALID_TEAM]}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user_queue_assignment_workflow(queues, case)
                audit_trail_service.create(
                    actor=request.user, verb=AuditType.UNASSIGNED, target=case,
                )

            return JsonResponse(data={"queues_removed": queue_names}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(
                data={"errors": {"queues": [Cases.UnassignQueues.NO_QUEUES]}}, status=status.HTTP_400_BAD_REQUEST
            )


class AdditionalContacts(ListCreateAPIView):
    queryset = Party.objects.additional_contacts()
    serializer_class = AdditionalContactSerializer
    pagination_class = None
    authentication_classes = (GovAuthentication,)

    def get_serializer_context(self):
        return {"organisation_pk": get_case(self.kwargs["pk"]).organisation.id}

    def perform_create(self, serializer):
        super().perform_create(serializer)
        audit_trail_service.create(
            actor=self.request.user,
            verb=AuditType.ADD_ADDITIONAL_CONTACT_TO_CASE,
            target=get_case(self.kwargs["pk"]),
            payload={"contact": serializer.data["name"]},
        )


class RerunRoutingRules(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):
        """
        Reruns routing rules against a given case, in turn removing all existing queues, and user assignments,
            and starting again from scratch on the given status
        Audits who requests the rules to be rerun
        """
        case = get_case(pk)

        audit_trail_service.create(
            actor=request.user, verb=AuditType.RERUN_ROUTING_RULES, target=case,
        )

        run_routing_rules(case)

        return JsonResponse(data={}, status=status.HTTP_200_OK)
