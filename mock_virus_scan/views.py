from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser

from django.http import JsonResponse, HttpResponseBadRequest


class Scan(APIView):
    parser_classes = (MultiPartParser,)
    EICAR_TEST = b"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"  # noqa

    def post(self, request):
        if len(request.FILES) != 1:
            return HttpResponseBadRequest("Provide a single file")

        uploaded_file = request.FILES["file"]

        if uploaded_file.file.read() == self.EICAR_TEST:
            return JsonResponse({"malware": True})

        return JsonResponse({"malware": False})
