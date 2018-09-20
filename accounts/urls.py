from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from .views.api import RegisterView, VerifyOptTokenView, ForgotPasswordRequestView, ForgotPasswordRequestValidateView, ChangeForgotPasswordView, ChangePasswordView

app_name = 'accounts'


urlpatterns = [
    url(r'^register/$', RegisterView.as_view(), name='register'),
    url(r'^otpverify/(?P<encoded_token>.+)/$', VerifyOptTokenView.as_view(), name='otpverify'),
    url(r'^login/$', auth_views.login, {'template_name': 'layouts/login.html', 'redirect_authenticated_user': True}, name='login'),
    url(r'^logout/$', auth_views.logout, {"next_page":"accounts:login"}, name='logout'),
    url(r'^forgot-password-request-otp/verify/$', ForgotPasswordRequestView.as_view(),
        name='forgot-password-request-otp'),
    url(r'^forgot-password-otp/verify/(?P<encoded_token>.+)/$',
        ForgotPasswordRequestValidateView.as_view(),
        name='forgot-password-request-otp-verify'),
    url(r'^forgot-password/reset/(?P<encoded_token>.+)/$',
        ChangeForgotPasswordView.as_view(), name='forgot-password-reset'),
    url(r'^change-password/$', ChangePasswordView.as_view(),
        name="user_change_password"),
    url(r'^admin/', admin.site.urls),
]