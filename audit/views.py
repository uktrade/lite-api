import json

from django.http import JsonResponse
from rest_framework.views import APIView
from reversion.models import Version, Revision


class AuditDetail(APIView):
    """
    Retrieve a model's history.
    """
    def get(self, request, type, pk):
        version_record = Version.objects.filter(object_id=pk).order_by('-revision_id')
        versions = []

        for version in version_record:
            _revision_object = Revision.objects.get(id=version.revision_id)
            data = {
                'date_updated': _revision_object.date_created,
                'data': json.loads(version.serialized_data)[0]['fields']
            }

            versions.append(data)

        return JsonResponse(data={'changes': versions})
