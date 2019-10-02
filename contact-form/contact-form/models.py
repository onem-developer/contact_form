from django.db import models


class AppAdmin(models.Model):
    admin_id = models.BigIntegerField()
    company_name = models.CharField(max_length=50)
    company_email = models.CharField(max_length=50)
    email_token = models.CharField(max_length=50)
