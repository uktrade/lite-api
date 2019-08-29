from django.urls import path

from goodstype import views

app_name = 'goodstype'

urlpatterns = [
    path('', views.GoodsTypeList.as_view(), name='goodstypes-list'),
    path('<uuid:pk>/', views.GoodsTypeDetail.as_view(), name='goodstypes-detail'),
    # ex: /goods/<uuid:pk>/activity/
    path('<uuid:pk>/activity/', views.GoodsTypeActivity.as_view(), name='activity'),
]
