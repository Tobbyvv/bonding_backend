# Generated by Django 3.1.3 on 2021-04-14 12:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20210227_2208'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheduletime',
            name='schedule',
        ),
        migrations.DeleteModel(
            name='Schedule',
        ),
        migrations.DeleteModel(
            name='ScheduleTime',
        ),
    ]