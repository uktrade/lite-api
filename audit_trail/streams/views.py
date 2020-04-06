from django.http import JsonResponse
from rest_framework.decorators import api_view

from audit_trail.streams.service import get_stream


def get_next_page_url(request, n):
    return request.build_absolute_uri("/").strip("/") + "/audit-trail/streams/{n}".format(n=n)


@api_view(["GET"])
def streams(request, timestamp):
    stream = get_stream(timestamp)

    return JsonResponse(
        {
            "@context": [
                "https://www.w3.org/ns/ettystreams",
                {"dit": "https://www.trade.gov.uk/ns/activitystreams/v1"},
            ],
            "orderedItems": stream["data"],
            **({"next": get_next_page_url(request, stream["next_timestamp"])} if len(stream["data"]) > 0 else {}),
        }
    )
