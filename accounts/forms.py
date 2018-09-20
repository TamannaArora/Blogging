from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.core.validators import RegexValidator, validate_email
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as trans
from mysite.core.fields import OtpField
from mysite.core.validators import validate_password
from . import message
from .models import User, UserSecurityToken
from mysite.core.string import Hash
from django.utils import timezone
from accounts.utils import RegistrationStep

class RegistrationForm(forms.ModelForm):
    firstname = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                                 'placeholder': trans('Enter your firstname')}))
    lastname = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                                 'placeholder': trans('Enter your lastname')}))
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                                 'placeholder': trans('Enter the Password')}),
                               label=_('Password'),
                               validators=[validate_password, ],
                               min_length=6,
                               error_messages={'min_length': message.PASSWORD_CHARACTER_LENGTH,
                                               "required": message.FIELD_REQUIRED,
                                               'password_mismatch': message.PASSWORD_MISMATCH_FIELDS})
    confirm_password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                                         'placeholder': trans('Confirm your Password')}),
                                        label=_('Confirm Password'),
                                        validators=[validate_password, ],
                                        min_length=6,
                                        error_messages={'min_length': message.PASSWORD_CHARACTER_LENGTH,
                                                       "required": message.FIELD_REQUIRED,
                                                       'password_mismatch': message.PASSWORD_MISMATCH_FIELDS})
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                                 'placeholder': trans('Enter your Email')}),
                             label=_("Email"), required=True,
                             error_messages={'required': message.FIELD_REQUIRED,
                                             'invalid': message.USER_INVALID_EMAIL_ADDRESS})

    class Meta(object):
        ''' 
        Meta for Registration Form
        '''
        model = get_user_model()
        fields = ('email', 'firstname', 'lastname', 'password')

    def __init__(self, *args, **kwargs):
        self._encoded_token = None
        super(RegistrationForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        ''' 
        Validate Email Field 
        '''
        user_model = get_user_model()
        try:
            validate_email(self.cleaned_data['email'])
        except ValidationError:
            raise forms.ValidationError(message.USER_INVALID_EMAIL_ADDRESS)
        try:
            user_model.objects.get(email__iexact=self.cleaned_data['email'])
        except user_model.DoesNotExist:
            return self.cleaned_data['email']
        raise forms.ValidationError(message.USER_WITH_THIS_MAIL_ALREADY_EXISTS)

    def clean(self):
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('confirm_password')
        if (password1 and password2) and (password1 != password2):
            raise forms.ValidationError(
                self.fields['password'].error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return self.cleaned_data

    def save(self):
        data = self.cleaned_data

        user = User(email=data['email'], firstname=data['firstname'],
               lastname=data['lastname'])
        user.set_password(data['password'])
        user.is_active = False
        user.save()
        return user
        

    def send_activation_token(self, request):
        '''
        Send Activation Token
        '''
      
        token = UserSecurityToken.create_activation_token(
            self.cleaned_data['email'])
        token.send_verify_token_email(request)
        self.encoded_token = token.encoded_token
        return self

    def get_encoded_token(self):
        '''
        Get Encoded Token
        '''
        return self.encoded_token


class VerifyOtpForm(forms.Form):
    '''
    Verify Otp Form for varifying Email after signup

    '''
    otp_token = OtpField(field_length=4, error_messages={
        'required': message.OTP_VALIDATION_FIELD_REQUIRED, })
    class Meta(object):
        ''' 
        Meta for Registration Form
        '''
        model = get_user_model()
        fields = ('email', 'password')

    def __init__(self, request=None, encoded_token=None, *args, **kwargs):
        self.request = request
        self.encoded_token = encoded_token
        self._token_cache = None
        super(VerifyOtpForm, self).__init__(*args, **kwargs)


    def clean_otp_token(self):
        '''
        Clean Otp Token
        '''
        register_data = self.request.session.get(
            RegistrationStep.KEY_USER_SESSION_DATA)
        email = register_data['email']
        otp_token = self.cleaned_data['otp_token']
        try:
            self._token_cache = UserSecurityToken.objects.get(
                expire_date__gt=timezone.now(),
                token=int(otp_token), extras=email)
            token_hash = Hash.decrypt_string(
                self.encoded_token.encode('utf-8'))
            if not self._token_cache.token == token_hash.decode('utf-8'):
                raise forms.ValidationError(
                    message.OTP_TOKEN_INVALID_OR_EXPIRED)
        except UserSecurityToken.DoesNotExist:
            print ("except case")
            raise forms.ValidationError(
                message.OTP_INVALID)
        return otp_token

    def get_token(self):
        '''
        Return token
        '''
        return self._token_cache.token

    def save(self):
        '''
        Save
        ''' 
        data = self.request.session[RegistrationStep.KEY_USER_SESSION_DATA]
        user = get_user_model().objects.get(email=data['email'])
        user.is_active = True
        user.save()
        data.update(self.cleaned_data)
        self.request.session[RegistrationStep.KEY_USER_STATE] = RegistrationStep.USER_EMAIL_VERIFIED

class ForgotPasswordRequestForm(forms.Form):
    '''
    Forgot Password Request Form

    '''
    email = forms.EmailField(label=_("Email"), required=True,
                             error_messages={'required': message.FIELD_REQUIRED,
                                             'invalid': message.USER_INVALID_EMAIL_ADDRESS})

    def __init__(self, request=None, *args, **kwargs):
        self._token = None
        self._user_cache = None
        self.request = request
        super(ForgotPasswordRequestForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        '''
        Clean Email

        '''
        user_model = get_user_model()
        try:
            self._user_cache = user_model.objects.get(
                email__iexact=self.cleaned_data['email'])
            if not self._user_cache.is_active:
                raise forms.ValidationError(message.USER_ACCOUNT_NOT_ACTIVE)
        except user_model.DoesNotExist:
            raise forms.ValidationError(
                message.USER_ACCOUNT_NOT_EXISTS)
        return self.cleaned_data['email']

    def save(self):
        '''
        Save
        '''
        self._token = UserSecurityToken.create_forgot_password_token(
            self._user_cache)
        self._token.send_forgot_password_email(self.request)
        self.request.session['forgot_token'] = self._token.token
        return self

    def get_encoded_token(self):
        '''
        Return Encoded Token
        '''
        return self._token.encoded_token

class ForgotPasswordRequestValidateForm(forms.Form):
    '''
    Forgot Password Request Validate Form
    '''
    otp_token = OtpField(field_length=4)

    def __init__(self, request=None, encoded_token=None, *args, **kwargs):
        self.request = request
        self._encoded_token = encoded_token
        self._token_cache = None
        super(ForgotPasswordRequestValidateForm,
              self).__init__(*args, **kwargs)

    def clean_otp_token(self):
        '''
        Clean Otp Token
        '''
        # import pdb; pdb.set_trace()
        otp_token = self.cleaned_data['otp_token']
        try:
            self._token_cache = UserSecurityToken.objects.get(
                expire_date__gt=timezone.now(),
                token_type=UserSecurityToken.FORGOT_PASSWORD,
                token=otp_token)
            token_hash = Hash.decrypt_string(
                self._encoded_token.encode('utf-8'))
            if (not self._token_cache.token == token_hash.decode('utf-8')) and\
                    (not self.request.session['forgot_token'] == self._token_cache.token):
                raise forms.ValidationError(
                    message.OTP_TOKEN_INVALID_OR_EXPIRED)
        except UserSecurityToken.DoesNotExist:
            raise forms.ValidationError(
                message.OTP_INVALID)
        return otp_token

    def get_token(self):
        '''
        Get Token
        '''
        return self._token_cache.token

    def get_encoded_token(self):
        '''
        Get Encoded token
        '''
        return self._encoded_token

class ChangePasswordForm(forms.Form):
    '''
    Change Password Form
    '''
    error_messages = {
        'password_mismatch': message.PASSWORD_MISMATCH_FIELDS
    }
    password = forms.CharField(label=_('Password'),
                               validators=[validate_password],
                               min_length=6,
                               widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                 'placeholder': trans('New Password'),
                                                                 'aria-required': "true"}),
                               error_messages={'min_length': message.PASSWORD_CHARACTER_LENGTH,
                                               "required": message.FIELD_REQUIRED})

    confirm_password = forms.CharField(label=_('Password'),
                                       widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                         'placeholder': trans('Confirm Password'),
                                                                         'aria-required': "true"}),
                                       error_messages={"required": message.FIELD_REQUIRED})

    class Meta(object):
        ''' Meta '''
        model = get_user_model()
        fields = ('password', 'confirm_password')

    def __init__(self, request=None, token=None, encoded_token=None, *args, **kwargs):
        # self._encoded_token = encoded_token
        # self._token_cache = token
        self.request = request
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        # import pdb; pdb.set_trace()
        # if not self.request.session['forgot_token'] == self._token_cache.token:
        #     raise forms.ValidationError(
        #         message.OTP_TOKEN_ENCRYPTION_NOT_MATCH)
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('confirm_password')
        if (password1 and password2) and (password1 != password2):
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return self.cleaned_data

    def save(self):
        ''' 
        Save 
        '''
        self.request.user.set_password(self.cleaned_data['password'])
        self.request.user.save()
        # self.request.expire = timezone.now()
        # self.request.save()
        # del self.request.session['forgot_token']
        return self

