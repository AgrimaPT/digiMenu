# Generated by Django 5.1.4 on 2025-02-26 06:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dmenu_app', '0024_order_billed'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='combined_id',
            field=models.UUIDField(blank=True, default=None, null=True),
        ),
    ]
