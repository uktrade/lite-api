from django.http import JsonResponse
from rest_framework.views import APIView
from celery import current_app

from api.core.celery_tasks import debug_add


class HealthCheck(APIView):
    def get(self, request):
        queue = current_app.amqp.queues["celery"]
        task = debug_add.apply_async(args=[1, 2], expires=3, queue=queue)
        result = task.get(timeout=3)
        if result != 3:
            return JsonResponse(status_code=500, data={"result": "unexpected_result"})

        return JsonResponse(data={"result": "success"})
