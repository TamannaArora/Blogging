# Generated by Django 2.0.8 on 2018-09-06 07:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postpagecomments',
            name='page',
        ),
        migrations.DeleteModel(
            name='PostPageComments',
        ),
    ]
