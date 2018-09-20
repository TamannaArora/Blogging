'''
Accounts Admin
'''
from django.contrib import admin, messages as flash_messages
from django.utils import timezone
from django.contrib.admin import AdminSite
from django.contrib.admin.utils import unquote
from django.contrib.auth import update_session_auth_hash
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.auth.forms import (AdminPasswordChangeForm,
                                       UserChangeForm)
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.conf.urls import url
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from oauth2_provider.models import AccessToken
from accounts.models import (User, UserSecurityToken)

AdminSite.site_header = 'The PROJECT Administration'
AdminSite.site_title = 'The PROJECT'

csrf_protect_m = method_decorator(csrf_protect)
sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())

class CustomUserAdmin(admin.ModelAdmin):
    """
    Custom Admin class for Custom user model
    """

    def __init__(self, *args, **kwargs):
        super(CustomUserAdmin, self).__init__(*args, **kwargs)

    change_user_password_template = None

    form = UserChangeForm

    change_password_form = AdminPasswordChangeForm

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (('Personal info'), {
            'fields': ('firstname', 'lastname', 'mobile_number',)}),
        (('Permissions'), {'fields': ('is_staff', 'is_superuser',
                                      'is_app_user', 'is_active')}),
    )

    readonly_fields = ('username',)

    list_select_related = True

    list_display = ['email', 'firstname', 'lastname',
                    'username', 'is_active']

    list_display_links = ['email', 'firstname', 'lastname', 'username']

    actions = ['make_active', 'make_inactive',]

    search_fields = ['email', 'firstname', 'lastname', 'username', 'id',]

    list_filter = ('is_active',)

    ordering = ('-id',)

    def get_urls(self):
        return [
            url(r'^(.+)/password/$', self.admin_site.admin_view(self.user_change_password),
                name='auth_user_password_change'),
        ] + super(CustomUserAdmin, self).get_urls()

    def make_active(self, request, queryset):
        '''make_active from action'''
        queryset.update(is_active=True)
    make_active.short_description = "Make selected users as Active"

    def make_inactive(self, request, queryset):
        '''make_inactive from action'''
        user_access_tokens = AccessToken.objects.filter(user__in=queryset)
        for token in user_access_tokens:
            token.expires = timezone.now()
            token.save()
        queryset.update(is_active=False)
    make_inactive.short_description = "Make selected users as Inactive"

    @sensitive_post_parameters_m
    def user_change_password(self, request, user_id, form_url=''):
        ''' User Change Password '''
        if not self.has_change_permission(request):
            raise PermissionDenied
        user = self.get_object(request, unquote(user_id))
        if user is None:
            message = 'User does not exist.'
            raise Http404(message % {'name': force_text(self.model._meta.verbose_name),
                                     'key': escape(id), })
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                change_message = self.construct_change_message(
                    request, form, None)
                self.log_change(request, user, change_message)
                msg = 'Password successfully changed.'
                flash_messages.success(request, msg)
                update_session_auth_hash(request, form.user)
                return HttpResponseRedirect('..')
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {'fields': list(form.base_fields)})]
        admin_form = admin.helpers.AdminForm(form, fieldsets, {})
        context = {
            'title': 'Change password',
            'adminForm': admin_form,
            'form_url': form_url,
            'form': form,
            'is_popup': (IS_POPUP_VAR in request.POST or
                         IS_POPUP_VAR in request.GET),
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
        }
        context.update(admin.site.each_context(request))

        request.current_app = self.admin_site.name

        return TemplateResponse(request,
                                self.change_user_password_template or
                                'admin/auth/user/change_password.html',
                                context)

class AdminUserSecurityToken(admin.ModelAdmin):
    '''
    Admin User Security
    '''
    model = UserSecurityToken
    list_display = ['detail', 'token', 'token_type', 'expire_date', ]
    list_filter = ('token_type',)

    @staticmethod
    def detail(obj):
        ''' Details '''
        if obj.user:
            return obj.user.email
        return obj.extras

    detail.short_description = 'Token'

    def get_queryset(self, request):

        return UserSecurityToken.objects.filter(expire_date__gte=timezone.now()).\
            select_related('user').order_by('-pk')

#  Model admin objects..
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserSecurityToken, AdminUserSecurityToken)
