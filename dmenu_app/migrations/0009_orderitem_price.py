# Generated by Django 5.1.4 on 2025-01-07 05:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dmenu_app', '0008_remove_orderitem_price_alter_order_customer_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
