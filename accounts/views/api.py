from accounts.models import User
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.views.generic import TemplateView, ListView, DetailView, FormView, RedirectView
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from mysite.core.string import Hash
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from accounts.forms import RegistrationForm, VerifyOtpForm, ForgotPasswordRequestForm, ForgotPasswordRequestValidateForm, ChangePasswordForm
from django.utils import timezone
from django.contrib.auth import login as auth_login, authenticate
from ..models import UserSecurityToken
from django import forms
from ..import message
from django.contrib import messages as flash_messages
from mysite.core.decorators import anonymous_view, logged_user_view
from accounts.utils import RegistrationStep

class RegisterView(FormView):
    '''
    Register View
    '''
    form_class = RegistrationForm
    template_name = 'layouts/register.html' 
    

    # def form_invalid(self, form):
    #     import pdb; pdb.set_trace()
    #     return super(RegisterView, self).form_invalid(form)

    def form_valid(self, form):
        # import pdb; pdb.set_trace()
        user = form.save()
        form.send_activation_token(self.request)
        self.request.session[RegistrationStep.KEY_USER_SESSION_DATA] = form.cleaned_data
        self.request.session[RegistrationStep.KEY_USER_STATE] = RegistrationStep.USER_EMAIL_PASS
        group = Group.objects.get(name='User-Group')
        user.groups.add(group)
        success_url = reverse_lazy("accounts:otpverify", kwargs={
            'encoded_token': form.get_encoded_token()})
        return HttpResponseRedirect(success_url)


    # def get_success_url(self):
    #     return self.request.GET.get('redirect_to', self.success_url)

class VerifyOptTokenView(FormView):
    '''
    Verify Otp Token View

    '''
    form_class = VerifyOtpForm
    template_name = 'layouts/otp.html'
    

    def get_form_kwargs(self):
        data = super(VerifyOptTokenView, self).get_form_kwargs()
        data.update({'request': self.request,
                     'encoded_token': self.kwargs['encoded_token']})
        return data

    def get_context_data(self, **kwargs):
        data = super(VerifyOptTokenView, self).get_context_data(**kwargs)
        data.update(self.request.session.get('register_user', []))
        data['encoded_token'] = self.kwargs['encoded_token']
        return data

    def form_valid(self, form):
        ''' 
        Runs When Submitted form is invalid
        '''
        
        success_url = '/'
        form.save()
        user_data = self.request.session[RegistrationStep.KEY_USER_SESSION_DATA]
        user = authenticate(email=user_data['email'], password=user_data['password'])
        if user is not None:
            auth_login(self.request, user)
            return HttpResponseRedirect(success_url)
    


class ChangeForgotPasswordView(FormView):
    '''
    ChangeForgotPasswordView 
    '''
    form_class = ChangePasswordForm
    template_name = "layouts/change_forgot_password.html"

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        ''' 
        Dispatch method of a form

        '''
        try:
            return super(ChangeForgotPasswordView, self).dispatch(request, *args, **kwargs)
        except UserSecurityToken.DoesNotExist:
            flash_messages.success(
                self.request, message.OTP_TOKEN_ENCRYPTION_NOT_MATCH)
            return HttpResponseRedirect(reverse('login'))

    def get_form_kwargs(self):
        '''
        Returns Form Keyword Arguments
        '''
        data = super(ChangeForgotPasswordView, self).get_form_kwargs()
        search_vars = {
            'expire_date__gt': timezone.now(),
            'token_type': UserSecurityToken.FORGOT_PASSWORD
        }
        token = UserSecurityToken.get_token_by_encoded_token(self.kwargs['encoded_token'],
                                                             search_vars)
        data.update({'request': self.request,
                     'encoded_token': self.kwargs['encoded_token'],
                     'token': token})
        return data

    def form_valid(self, form):
        '''
        Runs when a form is valid
        '''
        form.save()
        return super(ChangeForgotPasswordView, self).form_valid(form)

    def get_success_url(self):
        '''
        Returns success url
        '''
        flash_messages.success(
            self.request, message.MESSAGE_CHANGE_PASSWORD_SUCCESS)
        return reverse('accounts:login')


class ForgotPasswordRequestView(FormView):
    ''' 
    ForgotPasswordRequestView 

    '''
    form_class = ForgotPasswordRequestForm
    template_name = "layouts/forgot-pswrd.html"

    def form_invalid(self, form):
        '''
        Runs when a form is invalid
        '''
        data = {'errors': dict([(k, [str(e) for e in v])
                                for k, v in form.errors.items()])}
        data['success'] = False
        return JsonResponse(data)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        ''' 
        Dispatch method of a form

        '''
        return super(ForgotPasswordRequestView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        '''
        Returns Form Keyword Arguments
        '''
        data = super(ForgotPasswordRequestView, self).get_form_kwargs()
        data.update({'request': self.request})
        return data

    def form_valid(self, form):
        '''
        Runs when a form is valid
        '''
        form.save()
        data = form.get_encoded_token()
        redirect_to = reverse('accounts:forgot-password-request-otp-verify', kwargs={
            'encoded_token': form.get_encoded_token()})
        return HttpResponseRedirect(redirect_to)



class ForgotPasswordRequestValidateView(FormView):
    ''' 
    ForgotPasswordRequestValidateView
    
    '''
    form_class = ForgotPasswordRequestValidateForm
    template_name = "layouts/otp.html"

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        ''' 
        Dispatch method of a form

        '''
        try:
            return super(ForgotPasswordRequestValidateView, self).dispatch(request, *args, **kwargs)
        except UserSecurityToken.DoesNotExist:
            flash_messages.success(
                self.request, message.OTP_TOKEN_INVALID_OR_EXPIRED)
            return HttpResponseRedirect(reverse('accounts:login'))

    def get_form_kwargs(self):
        '''
        Returns Form Keyword Arguments
        '''
        data = super(ForgotPasswordRequestValidateView, self).get_form_kwargs()
        data.update({'request': self.request,
                     'encoded_token': self.kwargs['encoded_token']})
        return data

    def get_context_data(self, **kwargs):
        data = super(ForgotPasswordRequestValidateView,
                     self).get_context_data(**kwargs)
        search_vars = {
            'expire_date__gt': timezone.now(),
            'token_type': UserSecurityToken.FORGOT_PASSWORD
        }
        token = UserSecurityToken.get_token_by_encoded_token(self.kwargs['encoded_token'],
                                                             search_vars)
        data.update({'token': token})
        return data

    def form_valid(self, form):
        '''
        Runs when a form is valid
        '''
        return_url = reverse('accounts:forgot-password-reset',
                             kwargs={'encoded_token': form.get_encoded_token()})
        return HttpResponseRedirect(return_url)

    def get_success_url(self):
        '''
        Returns success url
        '''
        return reverse('accounts:forgot-password-reset')

@logged_user_view(redirect_to=reverse_lazy('accounts:login'))
class ChangePasswordView(FormView):
    '''
    Change Password View

    '''
    form_class = ChangePasswordForm
    template_name = "layouts/change_forgot_password.html"
    success_url = reverse_lazy('accounts:login')

    def get_form_kwargs(self):
        data = super(ChangePasswordView, self).get_form_kwargs()
        data.update({'request': self.request})
        return data

    def form_valid(self, form):
        form.save()
        return super(ChangePasswordView, self).form_valid(form)
