'''app view'''
# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response


def view_site(request):
    '''default index view'''
    return render_to_response('app/index.html')
