# Generated by Django 3.1.3 on 2021-02-22 20:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_profile_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='university',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profile', to='profiles.university'),
        ),
        migrations.AlterField(
            model_name='university',
            name='admission',
            field=models.IntegerField(),
        ),
    ]
