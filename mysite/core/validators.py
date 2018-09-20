'''
Validators
'''

from __future__ import unicode_literals
from django.core.exceptions import ValidationError


# REGEX_URL = r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9]\.[^\s]{2,})$'
# REGEX_MOBILE_NUMBER = r'^\+?1?\d{9,16}$'

# YOUTUBE_URL_REGEX = r'^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$'

# YOUTUBE_DURATION_REGEX = r'^PT((?P<hours>\d+)H)?((?P<minutes>\d+)M)?((?P<seconds>\d+)S)?$'


def validate_password(password):
    ''' Validate Password '''
    if password is None:
        raise ValidationError('this cannot be blank ',
                              code='required', params={'password': 'password'})
    elif len(password) < 6:
        raise ValidationError('Must have atleast 6 chars ',
                              code='min_length', params={'password': 'password'})
    else:
        return password


# def safe_username(username, whitelist=None, blacklist=None):
#     ''' Safe Username '''
#     wordlist = get_reserved_wordlist()
#     whitelist = whitelist or set()
#     blacklist = blacklist or set()
#     wordlist = wordlist - whitelist
#     wordlist = wordlist.union(blacklist)
#     if username.lower() in wordlist:
#         raise ValidationError('this cannot be blank ',
#                               code='reservedkeyword', params={'username': 'username'})
#     else:
#         return username
