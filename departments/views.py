from django.http import JsonResponse, Http404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.parsers import JSONParser

from departments.libraries.get_department import get_department_by_pk
from departments.models import Department
from departments.serializers import DepartmentSerializer


class DepartmentList(APIView):
    """
    List all departments, or create a new department.
    """
    def get(self, request):
        departments = Department.objects.all().order_by('name')
        serializer = DepartmentSerializer(departments, many=True)
        return JsonResponse(data={'departments': serializer.data})

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = DepartmentSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'department': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class DepartmentDetail(APIView):

    def get_object(self, pk):
        try:
            department = Department.objects.get(pk=pk)
            return department
        except Department.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        department = get_department_by_pk(pk)

        serializer = DepartmentSerializer(department)
        return JsonResponse(data={'department': serializer.data})

    def put(self, request, pk):
        data = JSONParser().parse(request)
        serializer = DepartmentSerializer(self.get_object(pk), data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'department': serializer.data})
        return JsonResponse(data={'errors': serializer.errors},
                            status=400)
