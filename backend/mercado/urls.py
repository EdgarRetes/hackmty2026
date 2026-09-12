from django.urls import path

from . import views

urlpatterns = [
    path("invoices/<int:invoice_id>/offers/", views.create_offers, name="invoice-offers"),
    path(
        "invoice-batches/<int:batch_id>/offers/",
        views.batch_offers,
        name="invoice-batch-offers",
    ),
    path("offers/<int:offer_id>/accept/", views.accept_offer, name="offer-accept"),
]
