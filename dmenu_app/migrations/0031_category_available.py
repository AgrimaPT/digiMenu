# Generated by Django 5.1.4 on 2025-04-16 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dmenu_app', '0030_order_payment_method_alter_order_user_order_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='available',
            field=models.BooleanField(default=True),
        ),
    ]
