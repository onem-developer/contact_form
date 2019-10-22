### Quickstart

Works with Python 3.7. Preferably to work in a virtual environment, use [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io) to create a virtual environment.

1. `mkvirtualenv contact_form --python=`which python 3.7`
2. `sudo apt-get install python3.7-dev`

1. `git clone git@github.com:onem-developer/contact_form.git`
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py runserver`
7. `ngrok http 8000`

### Testing the app

Register the app on the ONEm developer portal (https://testtool.dhq.onem:6060/);
Set the callback URL to the forwarding address obtained from ngrok's output;
Go to https://testtool.dhq.onem/ and send the registered name with # in front.

### Important

1. Please access the app in admin mode first.(the request headers should contain
the `is_admin=True` flag) This will enable you to first configure the app, storing
info about the business/company like `app_name`, `company_email`, `email_token` etc.
2. The app name needs also to be saved in the `settings.py` file, found in the root of the project,
along with the email delivery endpoint:
```
API_URL = 'https://api.postmarkapp.com/email'
APP_NAME = '' # to be added by developer after registering the app with ONEm
```
In this template/example app we have used Postmark as a transactional emails delivery service,
however you can use any other similar service. In admin mode, the app will allow you
to override the email token so you can save a new token if neccessary.

### Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)
