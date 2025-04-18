# Generated by Django 5.1.4 on 2025-04-17 09:18

# from django.db import migrations


# class Migration(migrations.Migration):

#     dependencies = [
#         ('dmenu_app', '0035_profile_delete_userprofile'),
#     ]

#     operations = [
#     ]

# Generated migration file
from django.db import migrations

def create_profiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('dmenu_app', 'Profile')
    
    for user in User.objects.all():
        Profile.objects.get_or_create(user=user)

class Migration(migrations.Migration):
    dependencies = [
        # Add your dependencies here
        ('dmenu_app', '0035_profile_delete_userprofile'),
    ]

    operations = [
        migrations.RunPython(create_profiles),
    ]