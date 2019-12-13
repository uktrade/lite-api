from django.http import JsonResponse
from rest_framework import generics, status

from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.generated_documents.helpers import get_letter_templates_for_case
from cases.libraries.get_case import get_case
from conf import constants
from conf.authentication import GovAuthentication
from conf.helpers import str_to_bool
from conf.permissions import assert_user_has_permission
from letter_templates.helpers import generate_preview, get_paragraphs_as_html
from letter_templates.models import LetterTemplate
from letter_templates.serializers import LetterTemplateSerializer
from picklists.enums import PicklistType
from picklists.models import PicklistItem
from static.letter_layouts.models import LetterLayout


class LetterTemplatesList(generics.ListCreateAPIView):
    """
    Returns list of all letter templates or creates a letter template
    """

    authentication_classes = (GovAuthentication,)
    queryset = LetterTemplate.objects.all()
    serializer_class = LetterTemplateSerializer

    def get_queryset(self):
        case = self.request.GET.get("case")
        return get_letter_templates_for_case(get_case(pk=case)) if case else self.queryset

    def post(self, request, *args, **kwargs):
        assert_user_has_permission(request.user, constants.GovPermissions.CONFIGURE_TEMPLATES)
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data=serializer.data, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LetterTemplateDetail(generics.RetrieveUpdateAPIView):
    """
    Returns detail of a specific letter template
    """

    authentication_classes = (GovAuthentication,)
    queryset = LetterTemplate.objects.all()
    serializer_class = LetterTemplateSerializer

    def get(self, request, *args, **kwargs):
        template_object = self.get_object()
        template = self.get_serializer(template_object).data
        data = {"template": template}
        paragraphs = PicklistItem.objects.filter(
            type=PicklistType.LETTER_PARAGRAPH, id__in=template["letter_paragraphs"]
        )
        paragraph_text = get_paragraphs_as_html(paragraphs)

        if str_to_bool(request.GET.get("generate_preview")):
            data["preview"] = generate_preview(layout=template_object.layout.filename, text=paragraph_text)
            if "error" in data["preview"]:
                return JsonResponse(data=data["preview"], status=status.HTTP_400_BAD_REQUEST)

        if str_to_bool(request.GET.get("text")):
            data["text"] = "\n\n".join([paragraph.text for paragraph in paragraphs])

        if str_to_bool(request.GET.get('activity')):
            data["activity"] = audit_trail_service.get_obj_trail(template_object)

        return JsonResponse(data=data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        assert_user_has_permission(request.user, constants.GovPermissions.CONFIGURE_TEMPLATES)
        template_object = self.get_object()
        serializer = self.get_serializer(template_object, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            if request.data.get("name"):
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UPDATED_LETTER_TEMPLATE_NAME,
                    target=serializer.instance,
                    payload={
                        'old_name': template_object.name,
                        'new_name': serializer.instance.name,
                    }
                )
                
            if request.data.get("case_types"):
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UPDATED_LETTER_TEMPLATE_CASE_TYPES,
                    target=serializer.instance,
                    payload={
                        'case_types': request.data.get("case_types"),
                    }
                )

            return JsonResponse(serializer.data)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class TemplatePreview(generics.RetrieveAPIView):

    authentication_classes = (GovAuthentication,)

    def get(self, request, **kwargs):
        paragraphs = PicklistItem.objects.filter(
            type=PicklistType.LETTER_PARAGRAPH, id__in=request.GET.getlist("paragraphs")
        )
        layout = LetterLayout.objects.get(id=request.GET["layout"]).filename
        text = get_paragraphs_as_html(paragraphs)
        preview = generate_preview(layout, text=text)

        if "error" in preview:
            return JsonResponse(data=preview, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data={"preview": preview}, status=status.HTTP_200_OK)
