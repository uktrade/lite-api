import factory

from api.bookmarks.models import Bookmark


class BookmarkFactory(factory.django.DjangoModelFactory):
    description = "desc"
    filter_json = "{}"

    class Meta:
        model = Bookmark
