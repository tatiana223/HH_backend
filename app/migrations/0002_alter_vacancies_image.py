# Generated by Django 4.2.7 on 2024-10-09 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vacancies',
            name='image',
            field=models.URLField(blank=True, max_length=1024, null=True),
        ),
    ]
