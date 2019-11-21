from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.views import APIView

from cases.libraries.get_case import get_case
from conf.authentication import GovAuthentication
from letter_templates.helpers import get_html_preview, generate_preview, get_paragraphs_as_html
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
    serializer_class = LetterTemplateSerializer

    def get_queryset(self):
        case = self.request.GET.get("case")

        if case:
            return LetterTemplate.objects.filter(restricted_to=get_case(pk=case).type)

        return LetterTemplate.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            data["restricted_to"] = list(data["restricted_to"])
            return JsonResponse(data=data, status=status.HTTP_201_CREATED)

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
        data = {"template": self.get_serializer(template_object).data }
        if 'generate_preview' in request.GET and bool(request.GET['generate_preview']):
            data["preview"] = get_html_preview(template=template_object)
        return JsonResponse(data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)

        return JsonResponse({"errors": serializer.errors})


class TemplatePreview(APIView):
    authentication_classes = (GovAuthentication,)

    @staticmethod
    def get(request):
        paragraphs = PicklistItem.objects.filter(
            type=PicklistType.LETTER_PARAGRAPH,
            id__in=request.GET.getlist("paragraphs")
        )
        layout = LetterLayout.objects.get(id=request.GET["layout"]).filename
        preview = generate_preview(layout, {"content": get_paragraphs_as_html(paragraphs)})
        return JsonResponse({"preview": preview})
