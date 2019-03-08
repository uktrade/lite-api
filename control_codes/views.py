from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from control_codes.models import ControlCode
from control_codes.serializers import ControlCodeSerializer


@api_view(['GET'])
def control_codes_list(request):
    if request.method == 'GET':
        snippets = ControlCode.objects.all()
        serializer = ControlCodeSerializer(snippets, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def control_code_detail(request, id):
    if request.method == 'GET':
        snippets = ControlCode.objects.all()
        serializer = ControlCodeSerializer(snippets, many=True)
        return Response(serializer.data)
