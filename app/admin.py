'''App Admin'''
from django.contrib import admin
from app.models import EmailMessage

class AdminEmallMessage(admin.ModelAdmin):
    '''
    Admin Class for Email Message
    '''
    models = EmailMessage
    list_display = ['from_email', 'to_email', 'subject',
                    'sent_status', 'sent_date', 'create_date']

admin.site.register(EmailMessage, AdminEmallMessage)
