from django.urls import path
from .views import SetupDatabaseView

urlpatterns = [
    path('setup/', SetupDatabaseView.as_view(), name='setup-database'),
]
