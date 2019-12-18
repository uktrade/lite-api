from django.http import JsonResponse
from rest_framework import generics, status

from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.enums import CaseTypeEnum
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

        if str_to_bool(request.GET.get("activity")):
            data["activity"] = audit_trail_service.get_obj_trail(template_object)

        return JsonResponse(data=data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        assert_user_has_permission(request.user, constants.GovPermissions.CONFIGURE_TEMPLATES)
        template_object = self.get_object()
        old_case_types = set(template_object.case_types.all().values_list("name", flat=True))
        old_paragraphs = list(template_object.letter_paragraphs.all().values_list("id", "name"))
        old_layout_id = str(template_object.layout.id)
        old_layout_name = str(template_object.layout.name)
        old_name = template_object.name
        serializer = self.get_serializer(template_object, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            if request.data.get("name"):
                if old_name != request.data.get("name"):
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.UPDATED_LETTER_TEMPLATE_NAME,
                        target=serializer.instance,
                        payload={"old_name": old_name, "new_name": serializer.instance.name,},
                    )

            if request.data.get("case_types"):
                new_case_types = set([CaseTypeEnum.get_text(choice) for choice in request.data.get("case_types")])
                if new_case_types != old_case_types:
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.UPDATED_LETTER_TEMPLATE_CASE_TYPES,
                        target=serializer.instance,
                        payload={"old_case_types": sorted(old_case_types), "new_case_types": sorted(new_case_types),},
                    )

            if request.data.get("letter_paragraphs"):
                new_paragraphs = list(serializer.instance.letter_paragraphs.all().values_list("id", "name"))
                if set(new_paragraphs) != set(old_paragraphs):
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.UPDATED_LETTER_TEMPLATE_PARAGRAPHS,
                        target=serializer.instance,
                        payload={
                            "old_paragraphs": [p[1] for p in old_paragraphs],
                            "new_paragraphs": [p[1] for p in new_paragraphs],
                        },
                    )
                else:
                    for n, o in zip(new_paragraphs, old_paragraphs):
                        if n != o:
                            audit_trail_service.create(
                                actor=request.user,
                                verb=AuditType.UPDATED_LETTER_TEMPLATE_PARAGRAPHS_ORDERING,
                                target=serializer.instance,
                            )
                            break

            if request.data.get("layout"):
                new_layout = request.data.get("layout")
                if new_layout != old_layout_id:
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.UPDATED_LETTER_TEMPLATE_LAYOUT,
                        target=serializer.instance,
                        payload={"old_layout": old_layout_name, "new_layout": serializer.instance.layout.name},
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
