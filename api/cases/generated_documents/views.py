import logging

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response

from api.applications.models import BaseApplication
from api.applications.helpers import reset_appeal_deadline
from api.audit_trail.enums import AuditType
from api.audit_trail import service as audit_trail_service
from api.cases.enums import CaseDocumentState, AdviceType
from api.cases.generated_documents.helpers import (
    html_to_pdf,
    get_generated_document_data,
    get_decision_type,
    get_draft_licence,
)
from api.cases.models import BadSubStatus
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.generated_documents.serializers import (
    GeneratedCaseDocumentGovSerializer,
    GeneratedCaseDocumentExporterSerializer,
)
from api.cases.generated_documents.signing import sign_pdf
from api.cases.libraries.delete_notifications import delete_exporter_notifications
from api.cases.notify import notify_exporter_inform_letter
from api.core.authentication import GovAuthentication, SharedAuthentication
from api.core.decorators import authorised_to_view_application
from api.core.helpers import str_to_bool
from api.documents.libraries import s3_operations
from api.letter_templates.helpers import get_css_location
from lite_content.lite_api import strings
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.staticdata.statuses.enums import CaseSubStatusIdEnum
from api.users.models import GovUser


logger = logging.getLogger(__name__)


class GeneratedDocument(generics.RetrieveAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = GeneratedCaseDocumentGovSerializer

    def get_object(self):
        return GeneratedCaseDocument.objects.get(id=self.kwargs["dpk"], case=self.kwargs["pk"])


class GeneratedDocuments(generics.ListAPIView):
    authentication_classes = (SharedAuthentication,)
    serializer_class = GeneratedCaseDocumentExporterSerializer

    def get_queryset(self):
        pk = self.kwargs["pk"]
        user = self.request.user

        if hasattr(user, "exporteruser"):
            documents = GeneratedCaseDocument.objects.filter(case_id=pk, visible_to_exporter=True)
            delete_exporter_notifications(
                user=user.exporteruser,
                organisation_id=get_request_user_organisation_id(self.request),
                objects=documents,
            )
        else:
            documents = GeneratedCaseDocument.objects.filter(case_id=pk)

        return documents

    @transaction.atomic
    @authorised_to_view_application(GovUser)
    def post(self, request, pk):
        """
        Create a generated document
        """
        licence = None
        try:
            document = get_generated_document_data(request.data, pk, include_css=False)
        except AttributeError:
            return JsonResponse(
                data={"errors": ["Missing template or party doesn't exist"]}, status=status.HTTP_400_BAD_REQUEST
            )

        pdf_s3_key = s3_operations.generate_s3_key(document.template.name, "pdf")

        css_s3_key = pdf_s3_key.replace("pdf", "css")
        css_file_path = get_css_location(document.template.layout.filename)
        with open(css_file_path, "rb") as css_file:
            logger.debug("Uploading CSS document `%s`", css_s3_key)
            s3_operations.upload_bytes_file(raw_file=css_file, s3_key=css_s3_key)

        html_s3_key = pdf_s3_key.replace("pdf", "html")
        logger.debug("Uploading HTML document `%s`", html_s3_key)
        s3_operations.upload_bytes_file(raw_file=document.document_html, s3_key=html_s3_key)

        try:
            pdf = html_to_pdf(document.document_html, document.template.layout.filename, request.build_absolute_uri())
        except Exception:  # noqa
            return JsonResponse(
                {"errors": [strings.Cases.GeneratedDocuments.PDF_ERROR]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if document.template.include_digital_signature:
            document_signing = document.case.get_application_manifest().document_signing
            pdf = sign_pdf(
                pdf, document_signing["signing_reason"], document_signing["location"], document_signing["image_name"]
            )

        advice_type = get_decision_type(request.data.get("advice_type"), document.template)

        licence = get_draft_licence(document.case, advice_type)

        # base the document name on the template name and a portion of the UUID generated for the s3 key
        document_name = f"{pdf_s3_key[:len(document.template.name) + 6]}.pdf"

        visible_to_exporter = str_to_bool(request.data.get("visible_to_exporter"))
        # If the template is not visible to exporter this supersedes what is given for the document
        # Decision documents are also hidden until finalised (see FinaliseView)
        if not document.template.visible_to_exporter or request.data.get("advice_type"):
            visible_to_exporter = False

        try:
            with transaction.atomic():
                # Delete any pre-existing decision document if the documents have not been finalised
                # i.e. They are not visible to the exporter
                GeneratedCaseDocument.objects.filter(
                    case=document.case, advice_type=request.data.get("advice_type"), visible_to_exporter=False
                ).delete()

                generated_doc = GeneratedCaseDocument.objects.create(
                    name=document_name,
                    user=request.user.govuser,
                    s3_key=pdf_s3_key,
                    virus_scanned_at=timezone.now(),
                    safe=True,
                    type=CaseDocumentState.GENERATED,
                    case=document.case,
                    template=document.template,
                    text=document.text,
                    visible_to_exporter=visible_to_exporter,
                    advice_type=request.data.get("advice_type"),
                    licence=licence,
                )

                logger.debug("Uploading PDF document `%s`", pdf_s3_key)
                s3_operations.upload_bytes_file(raw_file=pdf, s3_key=pdf_s3_key)
        except Exception:  # noqa
            return JsonResponse(
                {"errors": [strings.Cases.GeneratedDocuments.UPLOAD_ERROR]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if advice_type == AdviceType.REFUSE:
            # Reset appeal deadline once refusal letter is (re)generated
            application = get_object_or_404(BaseApplication.objects.all(), pk=pk)
            reset_appeal_deadline(application)

        if advice_type in [AdviceType.REFUSE, AdviceType.NO_LICENCE_REQUIRED, AdviceType.INFORM]:
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.GENERATE_DECISION_LETTER,
                target=generated_doc.case,
                payload={"case_reference": generated_doc.case.reference_code, "decision": advice_type},
            )

        return JsonResponse(data={"generated_document": str(generated_doc.id)}, status=status.HTTP_201_CREATED)


class GeneratedDocumentPreview(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Get a preview of the document to be generated
        """
        document = get_generated_document_data(request.GET, pk)
        return Response(data={"preview": document.document_html})


NOTIFICATION_FUNCTIONS = {
    "inform_letter": notify_exporter_inform_letter,
}


class GeneratedDocumentSend(APIView):
    authentication_classes = (GovAuthentication,)

    def post(self, request, pk, document_pk):
        document = get_object_or_404(GeneratedCaseDocument.objects.filter(case_id=pk), pk=document_pk)
        document.visible_to_exporter = True
        document.save()

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.DECISION_LETTER_SENT,
            target=document.case,
            payload={"case_reference": document.case.reference_code, "decision": document.advice_type},
        )
        serialized_document = GeneratedCaseDocumentGovSerializer(document).data

        layout_name = document.template.layout.filename

        if layout_name == "inform_letter":
            try:
                document.case.set_sub_status(CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT)
            except BadSubStatus:
                pass  # Sub-status cannot be set.. This is only a side effect so do not raise the error

        if NOTIFICATION_FUNCTIONS.get(layout_name):
            NOTIFICATION_FUNCTIONS[layout_name](document.case)
            return Response(data={"notification_sent": True, "document": serialized_document})

        return Response(data={"notification_sent": False, "document": serialized_document})
