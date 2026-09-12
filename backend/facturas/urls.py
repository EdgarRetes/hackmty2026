from django.urls import path

from . import views

urlpatterns = [
    path("invoices/", views.invoice_list, name="invoice-list"),
    path("invoice-batches/", views.invoice_batch_list, name="invoice-batch-list"),
    path(
        "invoice-batches/<int:batch_id>/",
        views.invoice_batch_detail,
        name="invoice-batch-detail",
    ),
    path("invoices/<str:reference>/", views.invoice_detail, name="invoice-detail"),
]
