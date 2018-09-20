'''
Email reusable component
'''

from django.conf import settings
from django.core.mail import EmailMessage as DjangoMail
from django.template.loader import get_template
from app.models import EmailMessage
#from tasks.tasks import send_email


class Email(object):
    ''' Email Create Object '''

    def __init__(self, to, subject, html_message=None, cc=None, from_addr=None):
        self.to = to
        self.subject = subject
        self.html = html_message
        self.cc = cc
        self.from_addr = from_addr

    def html(self, html):
        ''' Html object '''
        self.html = html
        return self

    def from_address(self, from_address):
        ''' From Address '''
        self.from_addr = from_address
        return self

    def message_from_template(self, template_name, context, request=None):
        ''' Message Body '''
        self.html = get_template(template_name).render(context, request)
        return self

    def send(self):
        ''' Create mail object '''
        if not self.from_addr:
            self.from_addr = settings.EMAIL_DEFAULT
        if not self.html:
            raise Exception('You must provide a text or html body.')
        email_data = {
            'from_email': self.from_addr,
            'to_email': self.to,
            'cc': self.cc,
            'subject': self.subject,
            'html_message': self.html

        }
        email_obj = DjangoMail(
            subject = email_data['subject'],
            body = email_data['html_message'],
            from_email = email_data['from_email'],
            to = [email_data['to_email']],  
        )
        email_obj.content_subtype = "html"
        email_obj.send()

