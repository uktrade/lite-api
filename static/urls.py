from django.urls import path, include

app_name = 'static'

urlpatterns = [
    path('countries/', include('static.countries.urls')),
    path('quantity/', include('static.quantity.urls')),
]
