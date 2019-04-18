from django.urls import path

from goods import views

app_name = 'goods'

urlpatterns = [
    path('', views.GoodList.as_view(), name='goods'),
    path('<uuid:pk>/', views.GoodDetail.as_view(), name='good')
]
