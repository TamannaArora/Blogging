# Generated by Django 2.0.8 on 2018-09-07 12:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0009_auto_20180907_1246'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogpage',
            name='categories',
            field=models.ManyToManyField(blank=True, to='blog.BlogCategoryBlogPage'),
        ),
    ]
