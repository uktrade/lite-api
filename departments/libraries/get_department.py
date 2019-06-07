from django.http import Http404

from departments.models import Department


def get_department_by_pk(pk):
    try:
        return Department.objects.get(pk=pk)
    except Department.DoesNotExist:
        raise Http404