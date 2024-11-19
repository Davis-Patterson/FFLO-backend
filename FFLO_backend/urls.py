from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('Accounts.urls')),
    path('api/', include('Server.urls')),
    path('pay/', include('Payments.urls')),
    path('manage/', include('Common.urls'))
]
