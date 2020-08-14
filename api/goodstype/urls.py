from django.urls import path

from api.goodstype import views

app_name = "goodstype"

urlpatterns = [
    path("<uuid:pk>/", views.RetrieveGoodsType.as_view(), name="retrieve"),
]
