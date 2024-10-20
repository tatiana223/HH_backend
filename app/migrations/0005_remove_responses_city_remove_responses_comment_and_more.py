# Generated by Django 4.2.7 on 2024-10-20 16:38

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0004_responses_vacancy_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='responses',
            name='city',
        ),
        migrations.RemoveField(
            model_name='responses',
            name='comment',
        ),
        migrations.RemoveField(
            model_name='responses',
            name='disability',
        ),
        migrations.RemoveField(
            model_name='responses',
            name='resume',
        ),
        migrations.RemoveField(
            model_name='responses',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='responses',
            name='vacancy',
        ),
        migrations.RemoveField(
            model_name='responses',
            name='vacancy_name',
        ),
        migrations.AddField(
            model_name='responses',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='responses',
            name='formed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='responses',
            name='moderator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='moderated_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='responses',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='responses',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_requests', to=settings.AUTH_USER_MODEL),
        ),
    ]
