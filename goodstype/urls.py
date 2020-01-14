from django.urls import path

from goodstype import views

app_name = "goodstype"

urlpatterns = [
    path("<uuid:pk>/", views.GoodsTypeDetail.as_view(), name="goodstypes_detail"),
]
