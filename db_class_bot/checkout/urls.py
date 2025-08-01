from django.urls import path
from . import views

urlpatterns = [
    path('request/<id>', views.payment_request),
    path('verify/<invoice_id>/', views.payment_verify),
]