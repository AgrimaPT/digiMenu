# Generated by Django 5.1.4 on 2025-01-14 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dmenu_app', '0011_orderitem_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='has_pending_orders',
            field=models.BooleanField(default=False),
        ),
    ]
