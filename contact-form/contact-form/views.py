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
        user, created = User.objects.get_or_create(id=data['sub'])
        user.is_admin = data['is_admin']
        user.ext_app_name = data['ext_app_name']

        return user

    def to_response(self, content):
        response = Response(content=content)

        return HttpResponse(response.json(), content_type='application/json')

class HomeView(View):
    http_method_names = ['get', 'post']

    def get(self, request):

        # TODO: what if admin sends SKIP when db record is not previously created ?
        if self.get_user().is_admin:
            form_items = [
                FormItem(type=FormItemType.string,
                         name='company_name',
                         description='Let us know your company name.',
                         header='admin',
                         footer='Reply with company name or SKIP'),
                # TODO: validate email ?
                FormItem(type=FormItemType.string,
                         name='company_email',
                         description="Let us know your company's email address.",
                         header='admin',
                         footer='Reply with company email address or SKIP'),
                # TODO: validate token ?
                FormItem(type=FormItemType.string,
                         name='email_token',
                         description='Please provide your Postmark email token.',
                         header='admin',
                         footer='Reply with token or SKIP')
            ]

        else:
            form_items = [
                FormItem(type=FormItemType.string,
                         name='user_message',
                         description='What would you like to know/inquire?',
                         header='contact',
                         footer='Reply with your message'),
            ]

            if not self.get_user().email:
                form_items.append(
                    FormItem(type=FormItemType.string,
                             name='user_email',
                             description='Let us know your email address.',
                             header='contact',
                             footer='Reply with email address')
                )


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
                company_name=request.POST['company_name'],
                company_email=request.POST['company_email'],
                email_token=request.POST['email_token']
            )
            return self.to_response(
                Menu(body=[MenuItem('Your business details have been updated!')],
                     header='setup',
                     footer='Reply MENU')  # TODO: menu would bring the admin in the same setup wizard...
            )
        else:
            # TODO: we need to add `ext_app_name` in the JWT headers
            user = self.get_user()
            if not user.email:
                user.email = request.POST['user_email']
                user.save()
            
            #qs = AppAdmin.objects.filter(company_name=self.get_user().ext_app_name)
            qs = AppAdmin.objects.filter(company_name='yamaha')
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Postmark-Server-Token': qs[0].email_token
            }
            body = {
                'From': request.POST['user_email'],
                'To': qs[0]['company_email'],
                'Subject': 'Inquiry from:{username}'.format(username=self.get_user()),
                'TextBody': request.POST['user_message']
            }
            
            send_email = requests.post(settings.API_URL, header=header,json=body)

            if send_email.status_code == u'200':
                result_msg = u'Your email was successfully sent! You will shortly receive a response to your inquiry!'
            else:
                result_msg = u'An error occured. Please try again later!'
        
            return self.to_response(
                Menu(body=[MenuItem(description=result_msg)],
                     header='contact',
                     footer='todo')
            )
