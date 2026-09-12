from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("mercado", "0001_initial")]

    operations = [
        migrations.AddField(model_name="offer", name="accepted_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="offer", name="category", field=models.CharField(blank=True, max_length=50)),
        migrations.AddField(model_name="offer", name="created_at", field=models.DateTimeField(auto_now_add=True)),
        migrations.AddField(model_name="offer", name="expires_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="offer", name="financing_cost", field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name="offer", name="funding_time", field=models.CharField(default="24 horas", max_length=50)),
        migrations.AddField(model_name="offer", name="net_amount", field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name="offer", name="rank", field=models.PositiveSmallIntegerField(default=0)),
        migrations.AlterModelOptions(name="offer", options={"ordering": ["rank", "rate"]}),
    ]
