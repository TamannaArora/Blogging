'''
Accounts Models
'''
import itertools
import random
from django.db import models
from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser,
                                        PermissionsMixin,
                                        BaseUserManager, Group)
from django.utils.text import slugify
from django.utils import timezone
from mysite.core.email import Email
from mysite.core.string import Hash
from . import message


class UserManager(BaseUserManager):
    '''
    User Custom Manager
    '''

    def create_user(self, email=None, password=None):
        '''
        Create User
        '''
        if not email:
            raise ValueError('User must have an email address')
        user = self.model(email=self.normalize_email(email))
        user.is_active = True
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        '''
        Create Superuser
        '''
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    '''
    If no need to use UserGroups/Permissions then remove PermissionsMixin
    '''
    email = models.EmailField('Email Address', unique=True)
    firstname = models.CharField('First Name', max_length=20, db_index=True)
    lastname = models.CharField('Last Name', max_length=20, db_index=True)
    username = models.SlugField(max_length=254, unique=True, blank=True)
    mobile_number = models.CharField(
        'Mobile Number', max_length=20, null=True, blank=True)
    is_staff = models.BooleanField('Staff member', default=False)
    is_active = models.BooleanField('Active', default=False)
    is_superuser = models.BooleanField('Is a Super user', default=False)
    create_date = models.DateTimeField('Joined Time', auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)
    is_app_user = models.BooleanField('App User', default=False)
    objects = UserManager()
    

    def get_full_name(self):
        return '{0} {1}'.format(self.firstname, self.lastname)

    def __str__(self):
        return '{0} {1}'.format(self.firstname, self.lastname)

    def get_short_name(self):
        return '{0}'.format(self.firstname, )

    @staticmethod
    def create_username(firstname, lastname, email, seperator='-'):
        ''' Create Username '''
        username = None
        lenslug = 210
        if firstname:
            username = firstname + ' ' + lastname
        else:
            username = email
        if not len(username) > 210:
            lenslug = len(username)
        username = slugify(username)[0:lenslug]
        temp_username = username
        for itrvalue in itertools.count(1):
            if not User.objects.filter(username=username).exists():
                break
            username = "%s%s%d" % (slugify(temp_username), seperator, itrvalue)
        return username

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        '''
        Save Model
        '''
        if not self.username:
            self.username = User.create_username(
                self.firstname, self.lastname, self.email)
        return super(User, self).save(force_insert=False,
                                      force_update=False,
                                      using=None,
                                      update_fields=None)

    USERNAME_FIELD = 'email'

    class Meta:
        ''' User Class Meta '''
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        app_label = 'accounts'


class UserSecurityToken(models.Model):
    '''
    User Security Token
    '''
    FORGOT_PASSWORD = 1
    ACCOUNT_ACTIVATION_TOKEN = 2
    OTP_MOBILE = 3
    OTP_REGISTER_VERIFY_TOKEN = 4
    TOKEN_TYPE_CHOICE = (
        (FORGOT_PASSWORD, 'Forgotten Password'),
        (ACCOUNT_ACTIVATION_TOKEN, 'Account Activation Link'),
        (OTP_MOBILE, 'One Time Password'),
        (OTP_REGISTER_VERIFY_TOKEN, 'OTP Verify Token')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             null=True, blank=True, related_name='tokens', on_delete=models.CASCADE)
    token = models.CharField(max_length=150)
    token_type = models.SmallIntegerField(choices=TOKEN_TYPE_CHOICE)
    extras = models.CharField(max_length=200, null=True, blank=True)
    expire_date = models.DateTimeField()

    def __str__(self):
        if self.user:
            return self.user.email
        return self.extras

    @property
    def encoded_token(self):
        ''' Encoded token '''
        return Hash.encrypt_string(self.token).decode('utf-8')

    @staticmethod
    def create_otp(expiry_date, token_type, user=None, extras=None):
        '''
        Create Otp
        '''
        token = random.randint(1111, 9999)
        data = {
            'user': user,
            'token': '{0:04d}'.format(token),
            'token_type': token_type,
            'expire_date': expiry_date,
            'extras': extras
        }

        return UserSecurityToken.objects.create(**data)

    @staticmethod
    def create_forgot_password_token(user):
        '''
        create Forgot Password token
        '''
        expire = timezone.now() + timezone.timedelta(**settings.ACCOUNT_VERIFY_TOKEN_EXPIRE_IN)
        UserSecurityToken.objects.filter(user=user,
                                         expire_date__gte=timezone.now(),
                                         token_type=UserSecurityToken.FORGOT_PASSWORD).update(expire_date=timezone.now())
        return UserSecurityToken.create_otp(expire, UserSecurityToken.FORGOT_PASSWORD, user=user)

    @staticmethod
    def create_activation_token(email):
        '''
        creating activation token
        '''
        expire = timezone.now() + timezone.timedelta(**settings.ACCOUNT_VERIFY_TOKEN_EXPIRE_IN)
        UserSecurityToken.objects.filter(extras=email,
                                         expire_date__gte=timezone.now(),
                                         token_type=UserSecurityToken.ACCOUNT_ACTIVATION_TOKEN).update(expire_date=timezone.now())
        token = UserSecurityToken.create_otp(
            expire, UserSecurityToken.ACCOUNT_ACTIVATION_TOKEN, extras=email)
        return token

    @staticmethod
    def get_token_by_encoded_token(encoded_token, search_data=None):
        '''
        Token By Encoded Token
        '''
        search_data = search_data if search_data else {}
        encoded_token = Hash.decrypt_string(encoded_token.encode('utf-8'))
        search_data.update({
            'token': encoded_token.decode('utf-8')
        })
        return UserSecurityToken.objects.select_related('user').get(**search_data)

    def send_verify_token_email(self, request):
        ''' Verify TOken '''
        Email(self.extras,
              message.SUBJECT_ACCOUNT_ACTIVATION_TOKEN).message_from_template('accounts/email/account_activation_email.html',
                                                                              {'token': self.token}, request).send()
        return self

    def send_forgot_password_email(self, request):
        '''  Forgot Password Email '''
        Email(self.user.email,
              message.SUBJECT_FORGOT_PASSWORD).message_from_template('accounts/email/forgot_password_email.html',
                                                                     {'token': self.token,
                                                                      'firstname': self.user.firstname,
                                                                      'lastname': self.user.lastname}, request).send()
        return self