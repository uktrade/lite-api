from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view

from audit_trail.streams.service import get_stream


def get_next_page_url(request, n):
    return request.build_absolute_uri("/").strip("/") + "/audit_trail/streams/{n}".format(n=n)


@api_view(["GET"])
def streams(request, n):
    stream = get_stream(n)

    return JsonResponse(
        {
            "@context": [
                "https://www.w3.org/ns/ettystreams",
                {"dit": "https://www.trade.gov.uk/ns/activitystreams/v1"},
            ],
            "orderedItems": stream,
            **({"next": get_next_page_url(request, n + 1)} if len(stream) > 0 else {}),
        }
    )
