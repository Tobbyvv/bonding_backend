# Generated by Django 3.1.3 on 2021-02-27 11:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('meeting', '0009_auto_20210226_2248'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='meetinginvitecode',
            name='created_datetime',
        ),
    ]