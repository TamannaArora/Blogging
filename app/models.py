'''
App Models
'''
from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField
from tinymce.models import HTMLField

class EmailMessage(models.Model):
    '''
    Email Model
    '''

    PENDING = 1
    INPROGRESS = 2
    SENT = 3
    ERROR = 4

    STATUS_TYPE = (
        (PENDING, 'Pending'),
        (INPROGRESS, 'In-Progress'),
        (SENT, 'Sent'),
        (ERROR, 'Error')
    )

    from_email = models.CharField(
        max_length=255, default=settings.EMAIL_DEFAULT)
    to_email = models.EmailField(max_length=255)
    cc = ArrayField(models.EmailField(max_length=255), blank=True, null=True)
    subject = models.CharField(max_length=200, null=True, blank=True)
    html_message = HTMLField()
    tries = models.PositiveSmallIntegerField(default=0)
    error_detail = models.CharField(max_length=255, null=True, blank=True)
    sent_status = models.SmallIntegerField(
        choices=STATUS_TYPE, default=PENDING)
    sent_date = models.DateTimeField(null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.to_email
