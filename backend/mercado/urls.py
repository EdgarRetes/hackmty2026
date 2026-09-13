from django.urls import path

from . import views

urlpatterns = [
    path("invoices/<int:invoice_id>/offers/", views.create_offers, name="invoice-offers"),
    path(
        "invoice-batches/<int:batch_id>/offers/",
        views.batch_offers,
        name="invoice-batch-offers",
    ),
    path(
        "invoice-batches/<int:batch_id>/accept/",
        views.accept_batch_offer,
        name="invoice-batch-accept",
    ),
    path("offers/<int:offer_id>/accept/", views.accept_offer, name="offer-accept"),
    path("marketplace/", views.marketplace_opportunities, name="marketplace"),
    path("financier/portfolio/", views.financier_portfolio, name="financier-portfolio"),
]
