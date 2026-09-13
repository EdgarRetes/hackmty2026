from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("facturas", "0004_invoice_available_status"),
        ("facturas", "0004_invoicebatch_factoring_term_days"),
    ]

    operations = []
