from django.contrib import admin
from django.urls import path, include
from .views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('Accounts.urls')),
    path('api/', include('Server.urls')),
    path('pay/', include('Payments.urls')),
    path('', home),
]
