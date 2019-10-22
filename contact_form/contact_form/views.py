import onemsdk
import jwt
import requests


from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.views.generic import View as _View

from onemsdk.schema.v1 import (
    Response, Menu, MenuItem, Form, FormItem, FormItemType, FormMeta
)

from .models import AppAdmin


class View(_View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *a, **kw):
        return super(View, self).dispatch(*a, **kw)

    def get_user(self):
        token = self.request.headers.get('Authorization')
        if token is None:
            raise PermissionDenied

        data = jwt.decode(token.replace('Bearer ', ''), key='87654321')
        user, created = User.objects.get_or_create(id=data['sub'], username=str(data['sub']))
        user.is_admin = data['is_admin']

        return user

    def to_response(self, content):
        response = Response(content=content)

        return HttpResponse(response.json(), content_type='application/json')

class HomeView(View):
    http_method_names = ['get', 'post']

    def get(self, request):
        if self.get_user().is_admin:
            form_items = [
                FormItem(type=FormItemType.string,
                         name='app_name',
                         description="Let us know your app name.",
                         header='admin',
                         footer="Reply with app name without '#'"),
                FormItem(type=FormItemType.string,
                         name='company_email',
                         description="Let us know the company's email address.",
                         header='admin',
                         footer='Reply with company email address'),
                FormItem(type=FormItemType.string,
                         name='email_token',
                         description='Please provide your email delivery service token.',
                         header='admin',
                         footer='Reply with token')
            ]

        else:
            form_items = [
                FormItem(type=FormItemType.string,
                         name='user_message',
                         description='What would you like to know/inquire?',
                         header='contact',
                         footer='Reply with your message'),
                FormItem(type=FormItemType.string,
                         name='user_email',
                         description='Let us know your email address.',
                         header='contact',
                         footer='Reply with email address')
            ]


        form = Form(body=form_items,
                    method='POST',
                    path=reverse('home'),
                    meta=FormMeta(confirmation_needed=False,
                                  completion_status_in_header=False,
                                  completion_status_show=False))

        return self.to_response(form)

    def post(self, request):
        if self.get_user().is_admin:
            company_profile = AppAdmin.objects.get_or_create(
                admin_id=self.get_user().id,
                app_name=request.POST['app_name'].lower(),
                company_email=request.POST['company_email'],
                email_token=request.POST['email_token']
            )
            return self.to_response(
                Menu(body=[MenuItem('Your business details have been updated!')],
                     header='setup',
                     footer='Reply MENU')
            )
        else:
            user = self.get_user()
            if not user.email:
                user.email = request.POST['user_email']
                user.save()
            
            qs = AppAdmin.objects.filter(app_name=settings.APP_NAME)

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': qs[0].email_token
            }

            body = {
                'To': qs[0].company_email,
                'From': self.request.POST['user_email'],
                'Subject': u'Inquiry from: {user_email}'.format(
                    user_email=request.POST.get('user_email', user.email)
                ),
                'TextBody': request.POST['user_message']
            }
            
            send_email = requests.post(settings.API_URL, headers=headers, json=body)

            if send_email.status_code == 200:
                # send confirmation email to user
                body = {
                    'To': self.request.POST['user_email'],
                    'From': qs[0].company_email,
                    'Subject': u'Email delivered!',
                    'TextBody': u''.join([
                        'Your email was received by {company_email}!'.format(company_email=qs[0].company_email),
                        'We will get back to you as soon as possible'])
                }
                send_email = requests.post(settings.API_URL, headers=headers, json=body)

                result_msg = u'Your email was successfully sent! You will shortly receive a response to your inquiry!'
            else:
                result_msg = u'An error occured. Please try again later!'
        
            return self.to_response(
                Menu(body=[MenuItem(description=result_msg)],
                     header='contact',
                     footer='--Reply MENU')
            )
