# Generated by Django 2.0.8 on 2018-08-24 08:17

import django.contrib.postgres.fields
from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmailMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_email', models.CharField(default='nsitester1@gmail.com', max_length=255)),
                ('to_email', models.EmailField(max_length=255)),
                ('cc', django.contrib.postgres.fields.ArrayField(base_field=models.EmailField(max_length=255), blank=True, null=True, size=None)),
                ('subject', models.CharField(blank=True, max_length=200, null=True)),
                ('html_message', tinymce.models.HTMLField()),
                ('tries', models.PositiveSmallIntegerField(default=0)),
                ('error_detail', models.CharField(blank=True, max_length=255, null=True)),
                ('sent_status', models.SmallIntegerField(choices=[(1, 'Pending'), (2, 'In-Progress'), (3, 'Sent'), (4, 'Error')], default=1)),
                ('sent_date', models.DateTimeField(blank=True, null=True)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('modify_date', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
