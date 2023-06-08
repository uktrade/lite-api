from rest_framework import serializers
from rest_framework.fields import JSONField

from api.bookmarks.models import Bookmark


class BookmarksSerializer(serializers.ModelSerializer):
    filter_json = JSONField()

    class Meta:
        model = Bookmark
        fields = (
            "id",
            "filter_json",
            "user",
            "name",
            "description",
        )
