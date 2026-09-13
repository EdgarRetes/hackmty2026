from django.db import migrations, models


def mark_one_approved_invoice_available(apps, schema_editor):
    Invoice = apps.get_model("facturas", "Invoice")
    candidate = (
        Invoice.objects.filter(
            status="pending",
            batch__isnull=True,
            risk_assessments__decision="APPROVE",
        )
        .order_by("id")
        .first()
    )
    if candidate is not None:
        candidate.status = "available"
        candidate.save(update_fields=["status"])


def restore_pending_status(apps, schema_editor):
    Invoice = apps.get_model("facturas", "Invoice")
    Invoice.objects.filter(status="available").update(status="pending")


class Migration(migrations.Migration):
    dependencies = [("facturas", "0003_riskassessment_invoice_cfdi_uuid_invoice_currency_and_more")]

    operations = [
        migrations.AlterField(
            model_name="invoice",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("available", "Available"),
                    ("in_auction", "In auction"),
                    ("funded", "Funded"),
                    ("paid", "Paid"),
                    ("overdue", "Overdue"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.RunPython(mark_one_approved_invoice_available, restore_pending_status),
    ]
