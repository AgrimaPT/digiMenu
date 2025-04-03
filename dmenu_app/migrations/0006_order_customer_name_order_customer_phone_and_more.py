# Generated by Django 5.1.4 on 2025-01-06 05:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dmenu_app', '0005_alter_category_sort_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='customer_name',
            field=models.CharField(default='a', max_length=255),
        ),
        migrations.AddField(
            model_name='order',
            name='customer_phone',
            field=models.CharField(default='1', max_length=15),
        ),
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending', max_length=20),
        ),
    ]
