from django.contrib import admin
from django.urls import path
from core.views import (
    upload_check,
    dashboard,
    transaction_list,
    edit_transaction,
    delete_transaction,
    manual_transaction,
    category_list,
    edit_category,
    delete_category, user_profile
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('upload_check/', upload_check, name='upload_check'),
    path('', dashboard, name='dashboard'),
    path('transactions/', transaction_list, name='transaction_list'),
    path('transactions/edit/<int:transaction_id>/', edit_transaction, name='edit_transaction'),
    path('transactions/delete/<int:transaction_id>/', delete_transaction, name='delete_transaction'),
    path('transactions/manual/', manual_transaction, name='manual_transaction'),
    path('categories/', category_list, name='category_list'),
    path('categories/edit/<int:category_id>/', edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', delete_category, name='delete_category'),
    path('user_profile/', user_profile, name='user_profile'),
]