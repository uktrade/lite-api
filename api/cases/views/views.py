from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http.response import JsonResponse, HttpResponse

from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.generics import ListCreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.views import APIView

from api.applications.models import GoodOnApplication
from api.applications.serializers.advice import (
    CountersignAdviceSerializer,
    CountryWithFlagsSerializer,
    CountersignDecisionAdviceSerializer,
)
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases import notify
from api.cases.enums import (
    CaseTypeSubTypeEnum,
    AdviceType,
    AdviceLevel,
)
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.generated_documents.serializers import AdviceDocumentGovSerializer
from api.cases.libraries.advice import group_advice
from api.cases.libraries.delete_notifications import delete_exporter_notifications
from api.cases.libraries.finalise import get_required_decision_document_types
from api.cases.libraries.get_case import get_case, get_case_document
from api.cases.libraries.get_destination import get_destination
from api.cases.libraries.get_ecju_queries import get_ecju_query
from api.cases.libraries.get_goods_type_countries_decisions import (
    good_type_to_country_decisions,
    get_required_good_type_to_country_combinations,
    get_existing_good_type_to_country_decisions,
)
from api.cases.libraries.post_advice import (
    post_advice,
    update_advice,
    check_if_final_advice_exists,
    check_if_user_cannot_manage_team_advice,
    case_advice_contains_refusal,
)
from api.cases.models import (
    Case,
    CaseDocument,
    EcjuQuery,
    EcjuQueryDocument,
    Advice,
    GoodCountryDecision,
    CaseAssignment,
    CaseReviewDate,
)
from api.cases.models import CountersignAdvice
from api.cases.notify import (
    notify_exporter_licence_issued,
    notify_exporter_licence_refused,
    notify_exporter_no_licence_required,
)
from api.cases.serializers import (
    CaseDocumentViewSerializer,
    CaseDocumentCreateSerializer,
    EcjuQueryCreateSerializer,
    CaseDetailBasicSerializer,
    CaseDetailSerializer,
    EcjuQueryGovSerializer,
    AdviceViewSerializer,
    CaseOfficerUpdateSerializer,
    ReviewDateUpdateSerializer,
    EcjuQueryExporterViewSerializer,
    EcjuQueryExporterRespondSerializer,
    EcjuQueryDocumentCreateSerializer,
    EcjuQueryDocumentViewSerializer,
)
from api.cases.service import get_destinations
from api.compliance.helpers import generate_compliance_site_case
from api.core import constants
from api.core.authentication import GovAuthentication, SharedAuthentication, ExporterAuthentication
from api.core.constants import GovPermissions
from api.core.exceptions import NotFoundError
from api.core.helpers import convert_date_to_string
from api.core.permissions import assert_user_has_permission
from api.documents.libraries.delete_documents_on_bad_request import delete_documents_on_bad_request
from api.documents.libraries.s3_operations import document_download_stream
from api.documents.models import Document
from api.goods.enums import GoodStatus
from api.goods.serializers import GoodOnApplicationSerializer
from api.licences.models import Licence
from api.licences.service import get_case_licences
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.parties.models import Party
from api.parties.serializers import PartySerializer, AdditionalContactSerializer
from api.queues.models import Queue
from api.staticdata.countries.models import Country
from api.staticdata.decisions.models import Decision
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.users.libraries.get_user import get_user_by_pk
from lite_content.lite_api import strings
from lite_content.lite_api.strings import Documents, Cases


class CaseDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieve a case instance
        """
        gov_user = request.user.govuser
        case = get_case(
            pk,
            prefetch_related=[
                "advice",
                "advice__user",
                "advice__user__baseuser_ptr",
                "advice__user__team",
                "advice__user__role",
                "advice__countersigned_by",
                "advice__countersigned_by__baseuser_ptr",
                "advice__countersigned_by__team",
                "advice__countersigned_by__role",
                "advice__denial_reasons",
                "advice__good",
                "advice__good__good",
                "countersign_advice",
                "flags",
                "queues",
                "copy_of",
                "copy_of__status",
            ],
            select_related=[
                "case_type",
                "case_officer",
                "case_officer__team",
            ],
        )
        data = CaseDetailSerializer(case, user=gov_user, team=gov_user.team).data

        if case.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
            data["data"]["destinations"] = get_destinations(case.id)  # noqa
        data["licences"] = get_case_licences(case)
        return JsonResponse(data={"case": data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """
        Change case status
        """
        case = get_case(pk)
        case.change_status(
            request.user, get_case_status_by_status(request.data.get("status")), request.data.get("note")
        )
        return JsonResponse(data={}, status=status.HTTP_200_OK)


class CaseDetailBasic(RetrieveAPIView):
    authentication_classes = (GovAuthentication,)
    queryset = Case.objects.all()
    serializer_class = CaseDetailBasicSerializer


class SetQueues(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        case = get_case(pk)
        request_queues = set(request.data.get("queues", []))
        queues = Queue.objects.filter(id__in=request_queues)
        note = request.data.get("note")

        if len(request_queues) > queues.count():
            queues_not_found = list(request_queues - set((str(id) for id in queues.values_list("id", flat=True))))
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
                payload={"queues": sorted([queue.name for queue in removed_queues]), "additional_text": note},
            )
        if new_queues:
            # Be careful when editing this audit trail event; we depend on it for
            # the flagging rule lite_routing.routing_rules_internal.flagging_rules_criteria:mod_consolidation_required_flagging_rule_criteria()
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.MOVE_CASE,
                target=case,
                payload={
                    "queues": sorted([queue.name for queue in new_queues]),
                    "queue_ids": sorted([str(queue.id) for queue in new_queues]),
                    "additional_text": note,
                    "case_status": case.status.status,
                },
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

    @transaction.atomic
    def post(self, request, pk):
        """
        Adds a document to the specified case
        """
        data = request.data

        for document in data:
            document["case"] = pk
            document["user"] = request.user.pk
            document["visible_to_exporter"] = False

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
            raise PermissionDenied()
        try:
            document = CaseDocument.objects.get(id=document_pk, case=case, visible_to_exporter=True)
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

    def post(self, request, pk):
        """
        Creates advice for a case
        """
        return post_advice(request, self.case, AdviceLevel.USER)

    def delete(self, request, pk):
        """
        Delete user level advice on a case for the current user.
        """
        self.advice.filter(user=request.user.govuser).delete()
        audit_trail_service.create(actor=request.user, verb=AuditType.CLEARED_USER_ADVICE, target=self.case)
        return JsonResponse(data={"status": "success"}, status=status.HTTP_200_OK)


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

        user_cannot_manage_team_advice = check_if_user_cannot_manage_team_advice(pk, request.user.govuser)
        if user_cannot_manage_team_advice:
            return user_cannot_manage_team_advice

        if self.team_advice.filter(team=request.user.govuser.team).count() == 0:
            team_id = self.request.user.govuser.team_id
            advice = self.advice.filter(user__team_id=team_id)
            group_advice(self.case, advice, request.user, AdviceLevel.TEAM)
            case_advice_contains_refusal(pk)

            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.CREATED_TEAM_ADVICE,
                target=self.case,
            )

            team_advice = Advice.objects.filter(case=self.case, team_id=team_id).order_by("-created_at")

        else:
            team_advice = self.team_advice

        serializer = AdviceViewSerializer(team_advice, many=True)
        return JsonResponse(data={"advice": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        """
        Creates advice for a case
        """
        user_cannot_manage_team_advice = check_if_user_cannot_manage_team_advice(pk, request.user.govuser)
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
        user_cannot_manage_team_advice = check_if_user_cannot_manage_team_advice(pk, request.user.govuser)
        if user_cannot_manage_team_advice:
            return user_cannot_manage_team_advice

        self.team_advice.filter(team=self.request.user.govuser.team).delete()
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

        final_advice = get_required_decision_document_types(get_case(pk))
        if not final_advice:
            return JsonResponse(data={"documents": {}}, status=status.HTTP_200_OK)

        advice_documents = {advice_type: {"value": advice_values[advice_type]} for advice_type in final_advice}

        if AdviceType.APPROVE in final_advice:
            # Get Licence document (Approve)
            licence = Licence.objects.get_draft_or_active_licence(pk)
            # Only cases with Approve/Proviso advice have a Licence
            if licence:
                try:
                    licence_document = GeneratedCaseDocument.objects.get(
                        advice_type=AdviceType.APPROVE, licence=licence
                    )
                    advice_documents[AdviceType.APPROVE]["document"] = AdviceDocumentGovSerializer(
                        licence_document
                    ).data
                except GeneratedCaseDocument.DoesNotExist:
                    pass
            # Remove Approve for looking up other decision documents below
            final_advice.remove(AdviceType.APPROVE)

        latest_documents = self.get_unique_documents(final_advice, pk)

        # add latest_documents to their respective advice_type
        for key, document in latest_documents.items():
            advice_documents[key]["document"] = document

        return JsonResponse(data={"documents": advice_documents}, status=status.HTTP_200_OK)

    def get_case_document(self, advice_type, pk):
        return (
            GeneratedCaseDocument.objects.filter(advice_type=advice_type, case__id=pk).order_by("-created_at").first()
        )

    def get_unique_documents(self, final_advice, pk):
        # Get other decision documents
        latest_documents = {}
        for advice_type in final_advice:
            # Remove duplicates for each advice type and filters it to only the most recent advice
            document = self.get_case_document(advice_type, pk)
            document = AdviceDocumentGovSerializer(
                document,
            ).data
            if document:
                latest_documents[advice_type] = document
        return latest_documents


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
            assert_user_has_permission(request.user.govuser, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)

            group_advice(self.case, self.team_advice, request.user, AdviceLevel.FINAL)
            final_advice = Advice.objects.filter(case=self.case).order_by("-created_at")
        else:
            final_advice = self.final_advice

        serializer = AdviceViewSerializer(final_advice, many=True)
        return JsonResponse(data={"advice": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        """
        Creates advice for a case
        """
        assert_user_has_permission(request.user.govuser, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)
        return post_advice(request, self.case, AdviceLevel.FINAL, team=True)

    def put(self, request, pk):
        """
        Updates advice for a case
        """
        assert_user_has_permission(request.user.govuser, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)
        return update_advice(request, self.case, AdviceLevel.FINAL)

    def delete(self, request, pk):
        """
        Clears team level advice and reopens the advice for user level for that team
        """
        assert_user_has_permission(request.user.govuser, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)
        self.final_advice.delete()
        # Delete GoodCountryDecisions as final advice is no longer applicable
        GoodCountryDecision.objects.filter(case_id=pk).delete()
        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.CLEARED_FINAL_ADVICE,
            target=self.case,
        )
        return JsonResponse(data={"status": "success"}, status=status.HTTP_200_OK)


class ECJUQueries(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        """
        Returns the list of ECJU Queries on a case
        """
        case_ecju_queries = (
            EcjuQuery.objects.select_related("team", "responded_by_user", "responded_by_user")
            .filter(case_id=pk)
            .order_by("created_at")
        )

        if hasattr(request.user, "exporteruser"):
            serializer = EcjuQueryExporterViewSerializer(case_ecju_queries, many=True)
            delete_exporter_notifications(
                user=request.user.exporteruser,
                organisation_id=get_request_user_organisation_id(request),
                objects=case_ecju_queries,
            )
        else:
            serializer = EcjuQueryGovSerializer(case_ecju_queries, many=True)

        return JsonResponse(data={"ecju_queries": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        """
        Add a new ECJU query
        """
        data = {**request.data, "case": pk, "raised_by_user": request.user.pk, "team": request.user.govuser.team.id}
        serializer = EcjuQueryCreateSerializer(data=data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            # Audit the creation of the query
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.ECJU_QUERY,
                action_object=serializer.instance,
                target=serializer.instance.case,
                payload={"ecju_query": data["question"]},
            )

            notify.notify_exporter_ecju_query(pk)

            return JsonResponse(data={"ecju_query_id": serializer.data["id"]}, status=status.HTTP_201_CREATED)


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
        serializer = EcjuQueryExporterViewSerializer(ecju_query)
        return JsonResponse(data={"ecju_query": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, pk, ecju_pk):
        """
        If not validate only Will update the ecju query instance, with a response, and return the data details.
        If validate only, this will return if the data is acceptable or not.
        """
        ecju_query = get_ecju_query(ecju_pk)
        if ecju_query.response:
            return JsonResponse(
                data={"error": f"Responding to closed {ecju_query.get_query_type_display()} is not allowed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {"response": request.data["response"], "responded_by_user": str(request.user.pk)}

        serializer = EcjuQueryExporterRespondSerializer(instance=ecju_query, data=data, partial=True)

        if serializer.is_valid():
            if "validate_only" not in request.data or not request.data["validate_only"]:
                serializer.save()
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ECJU_QUERY_RESPONSE,
                    action_object=serializer.instance,
                    target=serializer.instance.case,
                    payload={"ecju_response": data["response"]},
                )
                return JsonResponse(data={"ecju_query": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data={}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EcjuQueryAddDocument(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, **kwargs):
        """
        Returns a list of documents on the specified good
        """
        query_documents = EcjuQueryDocument.objects.filter(query_id=kwargs["query_pk"]).order_by("-created_at")
        serializer = EcjuQueryDocumentViewSerializer(query_documents, many=True)
        return JsonResponse({"documents": serializer.data})

    @transaction.atomic
    def post(self, request, **kwargs):
        """
        Adds a document to the specified good
        """
        ecju_query = get_ecju_query(kwargs["query_pk"])
        if ecju_query.response:
            return JsonResponse(
                {"error": "Adding document for a closed query is not allowed"}, status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data
        data["query"] = ecju_query.id
        data["user"] = request.user.pk

        serializer = EcjuQueryDocumentCreateSerializer(data=data)
        if serializer.is_valid():
            try:
                serializer.save()
            except Exception as e:  # noqa
                return JsonResponse(
                    {"errors": {"file": "We had an issue uploading your files. Try again later."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ecju_query.save()
            return JsonResponse({"documents": serializer.data}, status=status.HTTP_201_CREATED)

        delete_documents_on_bad_request(data)
        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EcjuQueryDocumentDetail(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, **kwargs):
        document = EcjuQueryDocument.objects.get(id=kwargs["doc_pk"])
        serializer = EcjuQueryDocumentViewSerializer(document)
        return JsonResponse({"document": serializer.data})

    @transaction.atomic
    def delete(self, request, **kwargs):
        document = EcjuQueryDocument.objects.get(id=kwargs["doc_pk"])
        if document.query.response:
            return JsonResponse(
                {"error": "Deleting document for a closed query is not allowed"}, status=status.HTTP_400_BAD_REQUEST
            )

        document.delete_s3()
        document.delete()
        return JsonResponse({"document": "deleted success"})


class GoodsCountriesDecisions(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        assert_user_has_permission(request.user.govuser, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)
        approved, refused = good_type_to_country_decisions(pk)
        return JsonResponse({"approved": list(approved.values()), "refused": list(refused.values())})

    @transaction.atomic
    def post(self, request, pk):
        assert_user_has_permission(request.user.govuser, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)

        data = {k: v for k, v in request.data.items() if v is not None}

        # Get list of all required item id's
        required_decisions = get_required_good_type_to_country_combinations(pk)
        required_decision_ids = set()
        for goods_type, country_list in required_decisions.items():
            for country in country_list:
                required_decision_ids.add(f"{goods_type}.{country}")

        if not required_decision_ids.issubset(data):
            missing_ids = required_decision_ids.difference(request.data)
            raise ParseError({missing_id: [Cases.GoodCountryMatrix.MISSING_ITEM] for missing_id in missing_ids})

        # Delete existing decision documents if decision changes
        existing_decisions = get_existing_good_type_to_country_decisions(pk)
        for decision_id in required_decision_ids:
            if (data.get(decision_id) != AdviceType.REFUSE) != existing_decisions.get(decision_id):
                # Proviso N/A as there is no proviso document type
                GeneratedCaseDocument.objects.filter(
                    case_id=pk, advice_type__in=[AdviceType.APPROVE, AdviceType.REFUSE], visible_to_exporter=False
                ).delete()
                break

        # Update or create GoodCountryDecisions
        for id in required_decision_ids:
            goods_type_id, country_id = id.split(".")
            value = data[id] == AdviceType.APPROVE
            GoodCountryDecision.objects.update_or_create(
                case_id=pk, goods_type_id=goods_type_id, country_id=country_id, defaults={"approve": value}
            )

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.UPDATED_GOOD_ON_DESTINATION_MATRIX,
            target=get_case(pk),
        )

        return JsonResponse(
            data={"good_country_decisions": list(required_decision_ids)}, status=status.HTTP_201_CREATED
        )


class OpenLicenceDecision(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        assert_user_has_permission(request.user.govuser, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)
        return JsonResponse(
            data={
                "decision": AdviceType.APPROVE
                if GoodCountryDecision.objects.filter(case_id=pk, approve=True).exists()
                else AdviceType.REFUSE
            }
        )


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


class CasesUpdateCaseOfficer(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def put(self, request):
        """
        Assigns a gov user as case officer to multiple cases
        """
        gov_user_pk = request.data.get("gov_user_pk")
        case_ids = request.data.get("case_ids")

        if not gov_user_pk or not case_ids:
            return JsonResponse(
                data={"errors": {"user": [Cases.CaseOfficerPage.NONE]}}, status=status.HTTP_400_BAD_REQUEST
            )

        data = {"case_officer": gov_user_pk}

        for case_pk in case_ids:
            case = get_case(case_pk)
            serializer = CaseOfficerUpdateSerializer(instance=case, data=data)

            if serializer.is_valid(raise_exception=True):
                user = get_user_by_pk(gov_user_pk)
                serializer.save()

                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ADD_CASE_OFFICER_TO_CASE,
                    target=case,
                    payload={
                        "case_officer": user.email if not user.first_name else f"{user.first_name} {user.last_name}"
                    },
                )
        return JsonResponse(data={}, status=status.HTTP_200_OK)


class FinaliseView(UpdateAPIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        """
        Finalise & grant a Licence
        """
        case = get_case(pk)

        # Check Permissions
        if CaseTypeSubTypeEnum.is_mod_clearance(case.case_type.sub_type):
            assert_user_has_permission(request.user.govuser, GovPermissions.MANAGE_CLEARANCE_FINAL_ADVICE)
        else:
            assert_user_has_permission(request.user.govuser, GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)

        required_decisions = get_required_decision_document_types(case)

        # Inform letter isn't required for finalisation
        if AdviceType.INFORM in required_decisions:
            required_decisions.remove(AdviceType.INFORM)

        # Check that each decision has a document
        # Excluding approve (done in the licence section below)
        generated_document_decisions = set(
            GeneratedCaseDocument.objects.filter(advice_type__isnull=False, case=case).values_list(
                "advice_type", flat=True
            )
        )

        if not required_decisions.issubset(generated_document_decisions):
            raise ParseError(
                {
                    f"decision-{decision}": [Cases.Licence.MISSING_DOCUMENTS]
                    for decision in required_decisions.difference(generated_document_decisions)
                }
            )

        return_payload = {"case": pk}

        # If a licence object exists, finalise the licence.
        try:
            licence = Licence.objects.get_draft_licence(pk)

            if AdviceType.APPROVE in required_decisions:
                # Check that a licence document has been created
                # (new document required for new licence)
                licence_document_exists = GeneratedCaseDocument.objects.filter(
                    advice_type=AdviceType.APPROVE, licence=licence
                ).exists()
                if not licence_document_exists:
                    raise ParseError({"decision-approve": [Cases.Licence.MISSING_LICENCE_DOCUMENT]})

                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.CREATED_FINAL_RECOMMENDATION,
                    target=case,
                    payload={
                        "case_reference": case.reference_code,
                        "decision": AdviceType.APPROVE,
                        "licence_reference": licence.reference_code,
                    },
                )

            licence.decisions.set([Decision.objects.get(name=decision) for decision in required_decisions])
            licence.issue()

            return_payload["licence"] = licence.id
            if Licence.objects.filter(case=case).count() > 1:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.REINSTATED_APPLICATION,
                    target=case,
                    payload={
                        "licence_duration": licence.duration,
                        "start_date": licence.start_date.strftime("%Y-%m-%d"),
                    },
                )
            generate_compliance_site_case(case)
        except Licence.DoesNotExist:
            # Do nothing if Licence doesn't exist
            pass

        # Finalise Case
        old_status = case.status.status
        case.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
        case.save()

        decisions = required_decisions.copy()

        if AdviceType.REFUSE in decisions:
            notify_exporter_licence_refused(case)

        if AdviceType.NO_LICENCE_REQUIRED in decisions:
            notify_exporter_no_licence_required(case)

        if AdviceType.APPROVE in decisions:
            notify_exporter_licence_issued(case)

        if AdviceType.APPROVE in decisions:
            decisions.remove(AdviceType.APPROVE)

        for decision in decisions:
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.CREATED_FINAL_RECOMMENDATION,
                target=case,
                payload={"case_reference": case.reference_code, "decision": decision, "licence_reference": ""},
            )

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.UPDATED_STATUS,
            target=case,
            payload={
                "status": {"new": case.status.status, "old": old_status},
                "additional_text": request.data.get("note"),
            },
        )

        # Show documents to exporter & notify
        documents = GeneratedCaseDocument.objects.filter(advice_type__isnull=False, case=case)
        documents.update(visible_to_exporter=True)
        for document in documents:
            document.send_exporter_notifications()

        return JsonResponse(return_payload, status=status.HTTP_201_CREATED)


class AdditionalContacts(ListCreateAPIView):
    serializer_class = AdditionalContactSerializer
    pagination_class = None
    authentication_classes = (GovAuthentication,)

    def get_queryset(self):
        return Party.objects.filter(case__id=self.kwargs["pk"])

    def get_serializer_context(self):
        return {"organisation_pk": get_case(self.kwargs["pk"]).organisation.id}

    def perform_create(self, serializer):
        party = serializer.save()
        case = get_case(self.kwargs["pk"])
        case.additional_contacts.add(party)
        audit_trail_service.create(
            actor=self.request.user,
            verb=AuditType.ADD_ADDITIONAL_CONTACT_TO_CASE,
            target=case,
            payload={"contact": serializer.data["name"]},
        )


class CaseApplicant(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        case = get_case(pk)
        applicant = case.submitted_by
        # compliance cases do not contain a person who submit them, as such we return empty details
        if not applicant:
            return JsonResponse({"name": "", "email": ""}, status=status.HTTP_200_OK)
        return JsonResponse(
            {"name": applicant.first_name + " " + applicant.last_name, "email": applicant.email},
            status=status.HTTP_200_OK,
        )


class NextReviewDate(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        """
        Sets a next review date for a case
        """
        case = get_case(pk)
        next_review_date = request.data.get("next_review_date")

        current_review_date = CaseReviewDate.objects.filter(case_id=case.id, team_id=request.user.govuser.team.id)
        data = {"next_review_date": next_review_date, "case": case.id, "team": request.user.govuser.team.id}

        if current_review_date.exists():
            current_review_date = current_review_date.get()
            old_next_review_date = current_review_date.next_review_date
            serializer = ReviewDateUpdateSerializer(instance=current_review_date, data=data)
        else:
            old_next_review_date = None
            serializer = ReviewDateUpdateSerializer(data=data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            team = request.user.govuser.team.name
            if old_next_review_date is None and next_review_date:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ADDED_NEXT_REVIEW_DATE,
                    target=case,
                    payload={"next_review_date": convert_date_to_string(next_review_date), "team_name": team},
                )
            elif old_next_review_date and next_review_date and str(old_next_review_date) != next_review_date:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.EDITED_NEXT_REVIEW_DATE,
                    target=case,
                    payload={
                        "new_date": convert_date_to_string(next_review_date),
                        "old_date": convert_date_to_string(old_next_review_date),
                        "team_name": team,
                    },
                )
            elif old_next_review_date and next_review_date is None:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.REMOVED_NEXT_REVIEW_DATE,
                    target=case,
                    payload={"team_name": team},
                )

            return JsonResponse(data={}, status=status.HTTP_200_OK)


class CountersignAdviceView(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request, **kwargs):
        case = get_case(kwargs["pk"])

        if CaseStatusEnum.is_terminal(case.status.status):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data
        advice_ids = [advice["id"] for advice in data]

        serializer = CountersignAdviceSerializer(
            Advice.objects.filter(id__in=advice_ids), data=data, many=True, partial=True
        )
        if not serializer.is_valid():
            return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        department = request.user.govuser.team.department

        if department is not None:
            department = department.name
        else:
            department = "department"

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.COUNTERSIGN_ADVICE,
            target=case,
            payload={"department": department},
        )

        return JsonResponse({"advice": serializer.data}, status=status.HTTP_200_OK)


class CountersignDecisionAdvice(APIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = CountersignDecisionAdviceSerializer

    def dispatch(self, request, *args, **kwargs):
        case = get_case(kwargs["pk"])
        if CaseStatusEnum.is_terminal(case.status.status):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().dispatch(request, *args, **kwargs)

    def audit_countersign(self, request, case, verb, payload):
        if payload.get("department"):
            payload["department"] = payload["department"].name
        else:
            payload["department"] = "department"

        audit_trail_service.create(
            actor=request.user,
            verb=verb,
            target=case,
            payload=payload,
        )

    def post(self, request, **kwargs):
        case = get_case(kwargs["pk"])
        data = request.data

        serializer = self.serializer_class(data=data, many=True)
        if not serializer.is_valid():
            return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        gov_user = request.user.govuser
        data = request.data
        case_countersignature = data[0]
        accepted = case_countersignature["outcome_accepted"]
        payload = {
            "firstname": gov_user.first_name,  # /PS-IGNORE
            "lastname": gov_user.last_name,  # /PS-IGNORE
            "department": gov_user.team.department,
            "order": case_countersignature["order"],
            "countersign_accepted": accepted,
        }
        if not accepted:
            payload["additional_text"] = case_countersignature["reasons"]

        self.audit_countersign(request, case, AuditType.LU_COUNTERSIGN, payload)

        return JsonResponse({"countersign_advice": serializer.data}, status=status.HTTP_201_CREATED)

    def put(self, request, **kwargs):
        case = get_case(kwargs["pk"])

        countersign_ids = [item["id"] for item in request.data]
        serializer = CountersignDecisionAdviceSerializer(
            CountersignAdvice.objects.filter(id__in=countersign_ids), data=request.data, partial=True, many=True
        )
        if not serializer.is_valid():
            return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        payload = {"department": request.user.govuser.team.department}
        self.audit_countersign(request, case, AuditType.COUNTERSIGN_ADVICE, payload)

        return JsonResponse({"countersign_advice": serializer.data}, status=status.HTTP_200_OK)


class GoodOnPrecedentList(ListAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = GoodOnApplicationSerializer

    def get_queryset(self):
        case = get_case(self.kwargs["pk"])
        gonas = GoodOnApplication.objects.filter(application=case).all()
        goods = {gona.good_id for gona in gonas}
        return (
            GoodOnApplication.objects.filter(good__in=goods, good__status=GoodStatus.VERIFIED)
            .exclude(application=case)
            .prefetch_related(
                "good",
                "good__flags",
                "good__control_list_entries",
                "application",
                "application__queues",
                "control_list_entries",
            )
        )
