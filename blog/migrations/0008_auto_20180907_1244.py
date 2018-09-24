# Generated by Django 2.0.8 on 2018-09-07 12:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_auto_20180907_1136'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='blogpage',
            name='categories',
        ),
        migrations.AddField(
            model_name='blogpage',
            name='categories',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='blog.BlogCategory'),
        ),
    ]