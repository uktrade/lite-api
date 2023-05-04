import uuid

from django.http.response import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from api.bookmarks import models
from api.bookmarks.serializers import BookmarksSerializer
from api.core.authentication import GovAuthentication


class Bookmarks(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        bookmarks = models.Bookmark.objects.filter(user_id=request.user.id)
        serializer = BookmarksSerializer(bookmarks, many=True)
        return JsonResponse({"user": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        new_bookmark = {"id": uuid.uuid4(), "user": request.user.govuser, **data}
        existing_bookmarks = models.Bookmark.objects.filter(
            url=new_bookmark["url"], user_id=new_bookmark.get("user_id")
        )
        if existing_bookmarks.exists():
            return JsonResponse(
                {"errors": [f"Bookmark for {new_bookmark['url']} already exists for user"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BookmarksSerializer(data=new_bookmark)

        if not serializer.is_valid():
            return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return JsonResponse({}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        existing_bookmarks = models.Bookmark.objects.filter(url=request.data["url"], user_id=request.data["user_id"])
        for bookmark in existing_bookmarks:
            bookmark.delete()

        return JsonResponse({}, status=status.HTTP_200_OK)
