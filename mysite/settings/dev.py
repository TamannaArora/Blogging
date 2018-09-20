from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ipe@oj_ro1ggs(!ln!lg51wz7hxbw$$=gdl9ha$h%r0-q*u^cy'

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['*'] 

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEBUG_MAIL = ''

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER =  'gridnsi@gmail.com'
EMAIL_HOST_PASSWORD = 'Grid@123456'
EMAIL_DEFAULT = 'gridnsi@gmail.com' 

SESSION_COOKIE_HTTPONLY = True

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_BROWSER_XSS_FILTER = True

CSRF_COOKIE_HTTPONLY = True

# WAGTAIL_FRONTEND_LOGIN_URL = '/accounts/login/'

HttpOnly = True

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# if DEBUG:

#     INSTALLED_APPS += ['log',
#                        ]

#     MIDDLEWARE += ['log.middleware.LoggingMiddleware']

#     LST_APP_FOR_LOGGING = ['app', 'accounts', 'oauth2_provider', ]

#     INTERNAL_IPS = ['172.16.16.196', '127.0.0.1']

try:
    from .local import *
except ImportError:
    pass
