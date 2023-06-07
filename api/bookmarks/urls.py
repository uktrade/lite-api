from django.urls import path

from api.bookmarks import views

app_name = "bookmarks"

urlpatterns = [
    path("", views.Bookmarks.as_view(), name="bookmarks"),
]
