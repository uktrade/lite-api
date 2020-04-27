from django.urls import path

from goodstype import views

app_name = "goodstype"

urlpatterns = [
    path("<uuid:pk>/", views.RetrieveGoodsType.as_view(), name="retrieve"),
]
