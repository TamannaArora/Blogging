'''
utitlity for all the apps
'''
from django.utils import timezone
from django.conf import settings
from oauth2_provider.models import Application, AccessToken, RefreshToken
from oauthlib.oauth2.rfc6749.tokens import random_token_generator

class RegistrationStep(object):
    ''' RegistrationStep '''

    USER_EMAIL_PASS = 1
    USER_EMAIL_VERIFIED = 2
    USER_PERSONAL_DETAIL = 3
    USER_SOCIAL_LINKS = 4
    USER_INTRESTS = 5
    USER_PROFILE_COMPLETE = 6

    KEY_USER_SESSION_DATA = 'register_user'
    KEY_USER_STATE = 'reg_step'

class UserAccessToken(object):
    ''' UserAccessToken '''

    def __init__(self, request, user, app_name):
        self.request = request
        self.user = user
        self.app_name = app_name

    def create_oauth_token(self):
        '''
        Create Outh token by user_id and application name
        '''
        scopes = 'read write'
        application = Application.objects.get(name=self.app_name)
        expires = timezone.now() + timezone.timedelta(days=settings.USER_TOKEN_EXPIRES)
        access_token = AccessToken.objects.create(
            user=self.user,
            token=random_token_generator(self.request),
            application=application,
            expires=expires,
            scope=scopes)

        RefreshToken.objects.create(
            user=self.user,
            token=random_token_generator(self.request),
            access_token=access_token,
            application=application
        )
        return access_token

    # def get_device_keys_from_request(self):
    #     '''
    #     get device keys from request
    #     '''
    #     device_id = self.request.data.get('device_id', None)
    #     device_token = self.request.data.get('device_token', None)
    #     device_type = self.request.data.get('device_type', None)
    #     return device_id, device_token, device_type

    # @classmethod
    # def add_device_detail(cls, device_type, device_id, user, device_token=None):
    #     '''
    #     add device detail
    #     '''
    #     device_info = {'user': user, 'device_id': device_id,
    #                    'device_type': device_type,
    #                    'device_token': device_token}
    #     UserDevice.objects.filter(
    #         device_token=device_token, is_device_token_valid=True).update(
    #             is_device_token_valid=False)
    #     UserDevice.objects.create(**device_info)