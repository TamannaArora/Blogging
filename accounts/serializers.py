''' SErialiser '''

import re
from django.conf import settings
from rest_framework import serializers
from django.forms import model_to_dict
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from oauth2_provider.models import AccessToken
from .utils import UserAccessToken
from accounts.models import UserSecurityToken
from . import message

class ForgotPasswordSerializer(serializers.ModelSerializer):
    ''' Forgot password '''
    token = serializers.CharField(read_only=True)
    token_type = serializers.IntegerField(read_only=True)
    expire_date = serializers.DateTimeField(read_only=True)
    email = serializers.EmailField(required=True, write_only=True)

    def __init__(self, *args, **kwargs):
        self.otp_sent = False
        super(ForgotPasswordSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context', None)
        if context:
            self.request = kwargs['context']['request']

    class Meta:
        ''' Meta information for forgot password serializer'''
        model = UserSecurityToken
        fields = "__all__"

    def validate_email(self, email_value):
        '''meta information for validating email'''
        try:
            user_instance = get_user_model().objects.filter(email__iexact=email_value).get()
            if user_instance.is_active:
                return email_value
            else:
                raise ValidationError(message.USER_ACCOUNT_NOT_ACTIVE)
        except get_user_model().DoesNotExist:
            raise ValidationError(message.USER_ACCOUNT_NOT_EXISTS)


    def create(self, validated_data):
        email = validated_data['email']
        user = get_user_model().objects.get(email__iexact=email)
        expiry_date = timezone.now() + timezone.timedelta(minutes=settings.FORGOT_PASSWORD_EXPIRE)
        instance = UserSecurityToken.create_otp(expiry_date, 3, user, extras=email)
        user_security_objects = UserSecurityToken.objects.filter(user_id=user.id, token_type=3).order_by('-id')[1:]
        UserSecurityToken.objects.filter(id__in=user_security_objects).update(expire_date=timezone.now())
        instance.send_forgot_password_email(self.request)
        self.otp_sent = True
        return instance

    @property
    def data(self):
        if self.otp_sent:
            return {'message': message.OTP_SENT}
        else:
            return {'message': message.OTP_SENT_FAILURE}


class ValidateOTPSerializer(serializers.ModelSerializer):
    '''
        OTP Validation
    '''
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)

    def __init__(self, *args, **kwargs):
        self.valid = False
        super(ValidateOTPSerializer, self).__init__(*args, **kwargs)

    class Meta:
        ''' Meta information for OTP validation serializer'''
        model = UserSecurityToken
        fields = ('email', 'otp')

    def validate_otp(self, otp_value):
        user_security_instance = UserSecurityToken.objects.filter(token=otp_value).first()
        if user_security_instance.expire_date > timezone.now():
            return otp_value
        else:
            raise ValidationError(message.OTP_EXPIRED)

    def update(self, *args, **kwargs):
        self.instance.expire_date = timezone.now()
        self.instance.save()
        self.valid = True
        return self.instance

    def create_reset_passwd_token(self, data):
        expiry_date = timezone.now() + timezone.timedelta(minutes=settings.VALIDATE_OTP_EXPIRE)
        user = get_user_model().objects.filter(email=data['email']).first()
        verify_token = UserSecurityToken.create_otp(expiry_date, UserSecurityToken.OTP_REGISTER_VERIFY_TOKEN,
                                                    user, extras=data['email'])
        return verify_token.token

    def to_representation(self, *args, **kwargs):
        if self.valid:
            verify_token = self.create_reset_passwd_token(self.context['request'].data)
            return {
                'message': message.OTP_VALIDATED_SUCCESSFULLY,
                'extras': verify_token
            }
        else:
            return super(ValidateOTPSerializer, self).to_representation(*args, **kwargs)


class ResetPasswordSerializer(serializers.ModelSerializer):
    '''
        Reset Password
    '''
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def __init__(self, *args, **kwargs):
        self.password_changed = False
        super(ResetPasswordSerializer, self).__init__(*args, **kwargs)

    class Meta:
        ''' Meta information for OTP validation serializer'''
        model = UserSecurityToken
        fields = ('email', 'otp', 'password',)

    def validate_password(self, password_value):
        ''' validates password '''
        if password_value and (len(password_value) < settings.VALIDATE_PASSWORD_MIN or len(password_value) > settings.VALIDATE_PASSWORD_MAX):
            raise serializers.ValidationError(message.PASSWORD_CHARACTER_LENGTH_API)
        return password_value

    def update(self, instance, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        user_instance = get_user_model().objects.filter(email__iexact=email).first()
        user_instance.set_password(password)
        user_instance.save()
        self.password_changed = True
        return user_instance

    def to_representation(self, *args, **kwargs):
        if self.password_changed:
            return {
                'message': message.RESET_PASSWORD
            }
        else:
            return super(ResetPasswordSerializer, self).to_representation(*args, **kwargs)

class AccessTokenSerializer(serializers.ModelSerializer):
    '''
    Serializer for Access Token
    '''
    class Meta:
        '''
        meta for access token
        '''
        model = AccessToken
        fields = ('token',)


class UserSerializer(serializers.ModelSerializer):
    '''
    serializer for user
    '''
    class Meta:
        '''
        meta for user
        '''
        model = get_user_model()
        fields = "__all__"
        extra_kwargs = {
            'password': {
                'write_only': True,
            },
        }



class RegisterUserSerialiser(UserSerializer):

    access_token = serializers.SerializerMethodField('get_user_access_token')
    username = serializers.CharField(required=True, max_length=25, validators=[RegexValidator(r'^[\d\w\-_\.]+$', flags=re.UNICODE)],
                                     error_messages={'required': message.FIELD_REQUIRED,
                                                     'invalid': message.USERNAME_REQUIRED,
                                                     'reservedkeyword': message.USERNAME_ALREADY_EXISTS,
                                                     'unique': message.USERNAME_ALREADY_EXISTS,
                                                     'max_length': message.USER_USERNAME_MAX_LENGTH, })
                                                     

    def __init__(self, *args, **kwargs):
        super(RegisterUserSerialiser, self).__init__(*args, **kwargs)
        context = kwargs.get('context', None)
        self.accesst_token = None

        if context:
            self.request = kwargs['context']['request']

    class Meta:
        model = get_user_model()
        fields = "__all__"
        extra_kwargs = {
            'password': {
                'write_only': True,
            },
        }

    def validate_email(self, email_value):
        '''validate email'''
        try:
            get_user_model().objects.filter(email__iexact=email_value).get()
            raise ValidationError("User already exist !")
        except get_user_model().DoesNotExist:
            return email_value

    def validate_username(self, username):
        '''
        Validate Username
        '''
        try:
            user_name = get_user_model().objects.filter(username__iexact=username).first()
            if user_name:
                raise ValidationError(message.USERNAME_ALREADY_EXISTS)
        except ValidationError:
            raise ValidationError(message.USERNAME_ALREADY_EXISTS)
        return username


    def create(self, validated_data):
        ''' create access token '''
        validated_data['is_active'] = True
        instance = get_user_model().objects.create(**validated_data)
        instance.set_password(validated_data['password'])
        instance.save()
        self.accesst_token = self.create_auth_token(instance)
        return instance

    def create_auth_token(self, instance):
        '''create auth token '''
        token_application_name = settings.APPLICATION_NAME
        user_access_token = UserAccessToken(
            self.request, instance, token_application_name)
        access_token = user_access_token.create_oauth_token()
        return access_token

    def get_user_access_token(self, user):
        '''get user access token '''
        return self.accesst_token.token



class LoginUserSerializer(serializers.Serializer):
    '''
    Login user serializer
    '''
    email = serializers.EmailField(required=True)
    access_token = serializers.CharField(read_only=True)
    password = serializers.CharField(required=True)

    class Meta:
        '''meta information for login user serializer'''
        fields = ('email', 'access_token' 'is_active',
                   'password',)
        extra_kwargs = {
            'password': {
                'write_only': True,
            },
        }

    def __init__(self, *args, **kwargs):
        super(LoginUserSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context', None)
        self.access_token = None
        self.user = None
        self.error_message = None
        if context:
            self.request = kwargs['context']['request']

    def authenticate(self, email, password):
        """
        authenticate user with provided crednetials
        """
        data = None
        try:
            user = get_user_model().objects.filter(email__iexact=email).get()
            if not user.is_active:
                raise ValidationError(message.USER_ACCOUNT_NOT_ACTIVE)
            #elif user.is_superuser:
             #   raise ValidationError(message.SUPERUSER)
            elif user.check_password(password):
                data = user
        except get_user_model().DoesNotExist:
            data = None
        return data

    def validate(self, validated_data):
        '''validating email'''
        self.user = self.authenticate(validated_data['email'], validated_data['password'])
        if self.user is None:
            raise ValidationError(message.LOGIN_AUTHENTICATION_INVALID)
        return validated_data

    def create(self, validated_data):
        token_application_name = settings.APPLICATION_NAME
        user_access_token = UserAccessToken(self.request, self.user, token_application_name)
        access_token = user_access_token.create_oauth_token()
        self.access_token = access_token.token
        return self
    
    @property
    def data(self):
        user = model_to_dict(self.user)
        user.pop('is_app_user')
        user.pop('password')
        user.pop('user_permissions')
        user.pop('is_superuser')
        user.pop('is_staff')
        user.pop('last_login')
        user.pop('is_active')
        user['access_token'] = self.access_token
        return {'message': message.USER_LOGGEDIN_SUCCESSFULLY, 'extras': user}



class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    class Meta:
        model = get_user_model()
        fields = "__all__"

    def validate_password(self, password_value):
        ''' validates password '''
        if password_value and (len(password_value) < settings.VALIDATE_PASSWORD_MIN or len(password_value) > settings.VALIDATE_PASSWORD_MAX):
            raise serializers.ValidationError(message.PASSWORD_CHARACTER_LENGTH_API)
        return password_value
    

class SignOutUserSerializer(serializers.ModelSerializer):
    '''serializer for user sign out'''

    class Meta:
        '''meta information for sign out user'''
        model = AccessToken
        fields = ('token', )
        extra_kwargs = {
            'token': {
                'write_only': True,
            }
        }

    def update(self, *args, **kwargs):
        self.instance.expires = timezone.now()
        self.instance.save()
        return self.instance

    def to_representation(self, *args, **kwargs):
        return {
            'message': message.LOGGED_OUT
        }


class EmailCheckSerializer(UserSerializer):
    def __init__(self, *args, **kwargs):
        super(EmailCheckSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context', None)
        self.accesst_token = None

        if context:
            self.request = kwargs['context']['request']

    class Meta:
        model = get_user_model()
        fields = ('email',)


class AccountActivationSerializer(serializers.ModelSerializer):
    ''' Forgot password '''
    token = serializers.CharField(read_only=True)
    token_type = serializers.IntegerField(read_only=True)
    expire_date = serializers.DateTimeField(read_only=True)
    email = serializers.EmailField(required=True, write_only=True)

    def __init__(self, *args, **kwargs):
        self.otp_sent = False
        super(AccountActivationSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context', None)
        if context:
            self.request = kwargs['context']['request']

    class Meta:
        ''' Meta information for forgot password serializer'''
        model = UserSecurityToken
        fields = '__all__'

    def validate_email(self, email_value):
        '''meta information for validating email'''
        try:
            user_instance = get_user_model().objects.filter(email__iexact=email_value).get()
            if not user_instance.is_active:
                return email_value
            else:
                raise ValidationError(message.ALREADY_REGISTER_USER)
        except get_user_model().DoesNotExist:
            user_instance = get_user_model().objects.create(
                email=email_value,
                firstname='test',
                lastname='user' 
                )
            user_instance.is_active = False
            user_instance.save()
            return email_value

    def create(self, validated_data):
        email = validated_data['email']
        user = get_user_model().objects.get(email__iexact=email)
        expiry_date = timezone.now() + timezone.timedelta(minutes=settings.FORGOT_PASSWORD_EXPIRE)
        instance = UserSecurityToken.create_otp(expiry_date, 2, user, extras=email)
        user_security_objects = UserSecurityToken.objects.filter(user_id=user.id, token_type=3).order_by('-id')[1:]
        UserSecurityToken.objects.filter(id__in=user_security_objects).update(expire_date=timezone.now())
        instance.send_verify_token_email(self.request)
        self.otp_sent = True
        return instance 

    @property
    def data(self):
        if self.otp_sent:
            return {'detail': message.OTP_SENT}
        else:
            return {'detail': message.OTP_SENT_FAILURE}



class CheckUserTokenSerializer(serializers.Serializer):
    '''check user token if expired or not'''

    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False)
    user_id = serializers.CharField(required=True, allow_null=True, allow_blank=True)

    def __init__(self, *args, **kwargs):
        super(CheckUserTokenSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context', None)
        if context:
            self.access_token = None
            self.user = None
            self.error_message = None
            self.request = kwargs['context']['request']

    def validate(self, validated_data):
        '''validating token'''
        user_id = int(validated_data['user_id'])
        self.user = get_user_model().objects.filter(id=user_id).first()
        if self.user:
            if self.request.user.id == user_id:
                return validated_data
            else:
                raise ValidationError(message.ACCESS_NOT_BELONGS_TO_USER)
        else:
            raise ValidationError(message.USER_ACCOUNT_NOT_EXISTS)
