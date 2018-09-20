# Generated by Django 2.0.8 on 2018-08-24 08:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email Address')),
                ('firstname', models.CharField(db_index=True, max_length=20, verbose_name='First Name')),
                ('lastname', models.CharField(db_index=True, max_length=20, verbose_name='Last Name')),
                ('username', models.SlugField(blank=True, max_length=254, unique=True)),
                ('mobile_number', models.CharField(blank=True, max_length=20, null=True, verbose_name='Mobile Number')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Staff member')),
                ('is_active', models.BooleanField(default=False, verbose_name='Active')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='Is a Super user')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Joined Time')),
                ('modify_date', models.DateTimeField(auto_now=True)),
                ('is_app_user', models.BooleanField(default=False, verbose_name='App User')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name_plural': 'Users',
                'verbose_name': 'User',
            },
        ),
        migrations.CreateModel(
            name='UserSecurityToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=150)),
                ('token_type', models.SmallIntegerField(choices=[(1, 'Forgotten Password'), (2, 'Account Activation Link'), (3, 'One Time Password'), (4, 'OTP Verify Token')])),
                ('extras', models.CharField(blank=True, max_length=200, null=True)),
                ('expire_date', models.DateTimeField()),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tokens', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
