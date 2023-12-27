# Generated by Django 3.1.3 on 2021-02-08 08:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('meeting', '0004_auto_20210203_1917'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfirmedMeeting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.PositiveIntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('place', models.CharField(max_length=10, null=True)),
                ('link', models.URLField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('duration_hour', models.PositiveSmallIntegerField(null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meetings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='plan',
            name='author',
        ),
        migrations.RemoveField(
            model_name='planinvitecode',
            name='connected_plan',
        ),
        migrations.DeleteModel(
            name='DummyPlan',
        ),
        migrations.DeleteModel(
            name='Plan',
        ),
        migrations.AddField(
            model_name='confirmedmeeting',
            name='meeting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confirmed_meetings', to='meeting.meeting'),
        ),
        migrations.AddField(
            model_name='planinvitecode',
            name='meeting',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='invite_code', serialize=False, to='meeting.meeting', unique=True),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='confirmedmeeting',
            unique_together={('meeting', 'key')},
        ),
    ]