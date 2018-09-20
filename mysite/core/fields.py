'''Fields '''
# pylint: disable=line-too-long
import os
from django import forms
from django.utils.translation import ugettext as _


class OtpFieldWidget(forms.MultiWidget):
    '''Ótp Field Widget'''

    def decompress(self, value):
        return str(value) if value else []

    def format_output(self, rendered_widgets):
        '''Format Output'''
        single_widget_template = u'<div class="col-md-6">{}</div>'
        wrapped_rendered_widgets = [single_widget_template.format(
            rendered_widget) for rendered_widget in rendered_widgets]
        return ' '.join(wrapped_rendered_widgets)


class OtpField(forms.MultiValueField):
    '''Ótp Field'''
    default_error_messages = {
        'required': _('Please enter a valid otp token.'),
    }

    def __init__(self, *args, **kwargs):
        error_messages = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            error_messages.update(kwargs['error_messages'])
        if 'field_length' in kwargs:
            self.char_length = kwargs.pop('field_length')
        else:
            self.char_length = 4
        if 'initial' not in kwargs:
            kwargs['initial'] = ''
        fields = list((forms.CharField(max_length=1, widget=forms.TextInput(attrs={
            'class': 'inputs', 'type': 'tel'}), error_messages={'invalid': error_messages['required']}) for i in range(1, self.char_length + 1)))
        super(OtpField, self).__init__(fields, *args, **kwargs)
        self.widget = OtpFieldWidget(
            widgets=[field.widget for field in fields])

    def compress(self, data_list):
        return ''.join(data_list)

