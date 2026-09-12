from django.urls import path

from . import views

urlpatterns = [
    path("invoices/", views.invoice_list, name="invoice-list"),
]
