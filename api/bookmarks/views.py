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
        new_bookmark = {**data}
        new_bookmark.update({"user": request.user.govuser})
        serializer = BookmarksSerializer(data=new_bookmark)

        if not serializer.is_valid():
            return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        data = serializer.data
        del data["user"]

        return JsonResponse(data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        bookmark_id = request.data["id"]
        bookmark = models.Bookmark.objects.filter(id=bookmark_id, user=request.user.govuser)

        if not bookmark.exists():
            return JsonResponse(
                {"errors": [f"Bookmark with id {bookmark_id} does not exist for this user"]},
                status=status.HTTP_404_NOT_FOUND,
            )
        bookmark[0].delete()

        return JsonResponse({}, status=status.HTTP_200_OK)

    def put(self, request):
        bookmark_id = request.data["id"]
        bookmark = models.Bookmark.objects.filter(id=bookmark_id, user=request.user.govuser)

        if not bookmark.exists():
            return JsonResponse(
                {"errors": [f"Bookmark with id {bookmark_id} does not exist for this user"]},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = request.data
        to_update = {k: data[k] for k in data if k in ("name", "description", "filter_json")}
        bookmark.update(**to_update)

        return JsonResponse({}, status=status.HTTP_200_OK)
