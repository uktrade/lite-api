from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F
from django.http.response import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.generics import ListCreateAPIView, UpdateAPIView
from rest_framework.views import APIView

from api.applications.serializers.advice import CountryWithFlagsSerializer
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.enums import (
    CaseTypeSubTypeEnum,
    AdviceType,
    AdviceLevel,
    CaseTypeTypeEnum,
    CaseTypeReferenceEnum,
)
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.generated_documents.serializers import AdviceDocumentGovSerializer
from api.cases.libraries.advice import group_advice
from api.cases.libraries.delete_notifications import delete_exporter_notifications
from api.cases.libraries.finalise import get_required_decision_document_types
from api.cases.libraries.get_case import get_case, get_case_document
from api.cases.libraries.get_destination import get_destination
from api.cases.libraries.get_ecju_queries import get_ecju_query, get_ecju_query_document
from api.cases.libraries.get_goods_type_countries_decisions import (
    good_type_to_country_decisions,
    get_required_good_type_to_country_combinations,
    get_existing_good_type_to_country_decisions,
)
from api.cases.libraries.post_advice import (
    post_advice,
    check_if_final_advice_exists,
    check_if_team_advice_exists,
    check_if_user_cannot_manage_team_advice,
    case_advice_contains_refusal,
)
from api.cases.models import (
    CaseDocument,
    EcjuQuery,
    EcjuQueryDocument,
    Advice,
    GoodCountryDecision,
    CaseAssignment,
    Case,
    CaseReviewDate,
)
from api.cases.serializers import (
    CaseDocumentViewSerializer,
    CaseDocumentCreateSerializer,
    EcjuQueryCreateSerializer,
    CaseDetailSerializer,
    EcjuQueryGovSerializer,
    AdviceViewSerializer,
    CaseOfficerUpdateSerializer,
    ReviewDateUpdateSerializer,
    EcjuQueryExporterViewSerializer,
    EcjuQueryExporterRespondSerializer,
    EcjuQueryMissingDocumentSerializer,
    EcjuQueryDocumentCreateSerializer,
    EcjuQueryDocumentViewSerializer,
    SimpleEcjuQueryDocumentViewSerializer,
)
from api.cases.service import get_destinations
from api.compliance.helpers import generate_compliance_site_case
from api.compliance.models import ComplianceVisitCase
from api.core import constants
from api.core.authentication import GovAuthentication, SharedAuthentication, ExporterAuthentication
from api.core.constants import GovPermissions
from api.core.exceptions import NotFoundError
from api.core.helpers import convert_date_to_string, str_to_bool
from api.core.permissions import assert_user_has_permission
from api.documents.libraries.delete_documents_on_bad_request import delete_documents_on_bad_request
from api.documents.libraries.s3_operations import document_download_stream
from api.documents.models import Document
from gov_notify import service as gov_notify_service
from gov_notify.enums import TemplateType
from gov_notify.payloads import EcjuCreatedEmailData, ApplicationStatusEmailData, EcjuComplianceCreatedEmailData
from api.licences.models import Licence
from api.licences.service import get_case_licences
from lite_content.lite_api.strings import Documents, Cases
from lite_content.lite_api.strings import EcjuQuery as EcjuQueryStrings
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.organisations.models import Site
from api.parties.models import Party
from api.parties.serializers import PartySerializer, AdditionalContactSerializer
from api.queues.models import Queue
from api.staticdata.countries.models import Country
from api.staticdata.decisions.models import Decision
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.users.libraries.get_user import get_user_by_pk


class CaseDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieve a case instance
        """
        gov_user = request.user.govuser
        case = get_case(pk)
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


class SetQueues(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        case = get_case(pk)
        request_queues = set(request.data.get("queues", []))
        queues = Queue.objects.filter(id__in=request_queues)
        note = request.data.get("note")

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
                payload={"queues": sorted([queue.name for queue in removed_queues]), "additional_text": note},
            )
        if new_queues:
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.MOVE_CASE,
                target=case,
                payload={"queues": sorted([queue.name for queue in new_queues]), "additional_text": note},
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
        if self.team_advice.filter(team=request.user.govuser.team).count() == 0:
            user_cannot_manage_team_advice = check_if_user_cannot_manage_team_advice(pk, request.user.govuser)
            if user_cannot_manage_team_advice:
                return user_cannot_manage_team_advice

            team = self.request.user.govuser.team_id
            advice = self.advice.filter(user__team_id=team)
            group_advice(self.case, advice, request.user, AdviceLevel.TEAM)
            case_advice_contains_refusal(pk)

            audit_trail_service.create(
                actor=request.user, verb=AuditType.CREATED_TEAM_ADVICE, target=self.case,
            )

            team_advice = Advice.objects.filter(case=self.case, team_id=team).order_by("-created_at")
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

        # Get other decision documents
        generated_advice_documents = GeneratedCaseDocument.objects.filter(advice_type__in=final_advice, case__id=pk)
        generated_advice_documents = AdviceDocumentGovSerializer(generated_advice_documents, many=True,).data
        for document in generated_advice_documents:
            advice_documents[document["advice_type"]["key"]]["document"] = document

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
            assert_user_has_permission(request.user.govuser, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)

            group_advice(self.case, self.team_advice, request.user, AdviceLevel.FINAL)

            audit_trail_service.create(
                actor=request.user, verb=AuditType.CREATED_FINAL_ADVICE, target=self.case,
            )
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

    def delete(self, request, pk):
        """
        Clears team level advice and reopens the advice for user level for that team
        """
        assert_user_has_permission(request.user.govuser, constants.GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)
        self.final_advice.delete()
        # Delete GoodCountryDecisions as final advice is no longer applicable
        GoodCountryDecision.objects.filter(case_id=pk).delete()
        audit_trail_service.create(
            actor=request.user, verb=AuditType.CLEARED_FINAL_ADVICE, target=self.case,
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

            # Send an email to the user(s) that submitted the application
            case_info = (
                Case.objects.annotate(email=F("submitted_by__baseuser_ptr__email"), name=F("baseapplication__name"))
                .values("id", "email", "name", "reference_code", "case_type__type", "case_type__reference")
                .get(id=pk)
            )

            # For each licence in a compliance case, email the user that submitted the application
            if case_info["case_type__type"] == CaseTypeTypeEnum.COMPLIANCE:
                emails = set()
                case_id = case_info["id"]
                link = f"{settings.EXPORTER_BASE_URL}/compliance/{pk}/ecju-queries/"

                if case_info["case_type__reference"] == CaseTypeReferenceEnum.COMP_VISIT:
                    # If the case is a compliance visit case, use the parent compliance site case ID instead
                    case_id = ComplianceVisitCase.objects.get(pk=case_id).site_case.id
                    link = f"{settings.EXPORTER_BASE_URL}/compliance/{case_id}/visit/{pk}/ecju-queries/"

                site = Site.objects.get(compliance__id=case_id)

                for licence in Case.objects.filter_for_cases_related_to_compliance_case(case_id):
                    emails.add(licence.submitted_by.email)

                for email in emails:
                    gov_notify_service.send_email(
                        email_address=email,
                        template_type=TemplateType.ECJU_COMPLIANCE_CREATED,
                        data=EcjuComplianceCreatedEmailData(
                            query=serializer.data["question"],
                            case_reference=case_info["reference_code"],
                            site_name=site.name,
                            site_address=str(site.address),
                            link=link,
                        ),
                    )
            else:
                gov_notify_service.send_email(
                    email_address=case_info["email"],
                    template_type=TemplateType.ECJU_CREATED,
                    data=EcjuCreatedEmailData(
                        application_reference=case_info["name"] or "",
                        case_reference=case_info["reference_code"],
                        link=f"{settings.EXPORTER_BASE_URL}/applications/{pk}/ecju-queries/",
                    ),
                )

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

        data = {"response": request.data["response"], "responded_by_user": str(request.user.pk)}

        serializer = EcjuQueryExporterRespondSerializer(instance=ecju_query, data=data, partial=True)

        if serializer.is_valid():
            if "validate_only" not in request.data or not request.data["validate_only"]:
                serializer.save()

                return JsonResponse(data={"ecju_query": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data={}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EcjuQueryDocumentCriteriaCheck(APIView):
    authentication_classes = (ExporterAuthentication,)

    def post(self, request, **kwargs):
        ecju_query = get_ecju_query(kwargs["query_pk"])
        data = request.data
        if data.get("has_document_to_upload"):
            document_to_upload = str_to_bool(data["has_document_to_upload"])
            if not document_to_upload:
                ecju_query.missing_document_reason = data["missing_document_reason"]
                serializer = EcjuQueryMissingDocumentSerializer(instance=ecju_query, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    ecju_query_detail = EcjuQueryCreateSerializer(ecju_query).data
                else:
                    return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            else:
                ecju_query.missing_document_reason = None
                ecju_query.save()
                ecju_query_detail = EcjuQueryCreateSerializer(ecju_query).data
        else:
            return JsonResponse(
                data={"errors": {"has_document_to_upload": [EcjuQueryStrings.DOCUMENT_CHECK_OPTION_NOT_SELECTED]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return JsonResponse(data={"ecju_query": ecju_query_detail}, status=status.HTTP_200_OK)


class EcjuQueryAddDocument(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns a list of documents on the specified good
        """
        query_documents = EcjuQueryDocument.objects.filter(query_id=pk).order_by("-created_at")
        serializer = EcjuQueryDocumentViewSerializer(query_documents, many=True)

        return JsonResponse({"documents": serializer.data})

    @transaction.atomic
    def post(self, request, **kwargs):
        """
        Adds a document to the specified good
        """
        import pdb; pdb.set_trace()
        ecju_query = get_ecju_query(kwargs["query_pk"])
        data = request.data

        for document in data:
            document["query"] = ecju_query.id
            document["user"] = request.user.pk

        serializer = EcjuQueryDocumentCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            try:
                serializer.save()
            except Exception as e:  # noqa
                return JsonResponse(
                    {"errors": {"file": EcjuQueryStrings.UPLOAD_FAILURE}}, status=status.HTTP_400_BAD_REQUEST
                )
            # Delete missing document reason as a document has now been uploaded
            ecju_query.missing_document_reason = None
            ecju_query.save()
            return JsonResponse({"documents": serializer.data}, status=status.HTTP_201_CREATED)

        delete_documents_on_bad_request(data)
        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EcjuQueryDocumentDetail(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk, doc_pk):
        """
        Returns a list of documents on the specified good
        """
        query = get_ecju_query(pk)
        query_document = get_ecju_query_document(query, doc_pk)
        serializer = EcjuQueryDocumentViewSerializer(query_document)
        return JsonResponse({"document": serializer.data})

    @transaction.atomic
    def delete(self, request, pk, doc_pk):
        """
        Deletes good document
        """
        import pdb; pdb.set_trace()
        query = get_ecju_query(pk)
        query_document = EcjuQueryDocument.objects.get(id=doc_pk)
        query_document.delete_s3()

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
            actor=request.user, verb=AuditType.UPDATED_GOOD_ON_DESTINATION_MATRIX, target=get_case(pk),
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

            licence.decisions.set([Decision.objects.get(name=decision) for decision in required_decisions])
            licence.issue()
            return_payload["licence"] = licence.id
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.GRANTED_APPLICATION
                if Licence.objects.filter(case=case).count() < 2
                else AuditType.REINSTATED_APPLICATION,
                target=case,
                payload={"licence_duration": licence.duration, "start_date": licence.start_date.strftime("%Y-%m-%d")},
            )
            generate_compliance_site_case(case)
        except Licence.DoesNotExist:
            # Do nothing if Licence doesn't exist
            pass

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
