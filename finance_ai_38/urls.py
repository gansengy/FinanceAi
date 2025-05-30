from django.contrib import admin
from django.urls import path
from core.views import upload_check, dashboard, transaction_list

urlpatterns = [
    path('admin/', admin.site.urls),
    path('upload_check/', upload_check, name='upload_check'),
    path('', dashboard, name='dashboard'),
    path('transactions/', transaction_list, name='transaction_list'),
]
