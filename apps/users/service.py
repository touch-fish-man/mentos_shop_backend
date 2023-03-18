import random
import string
import time

from django.core.mail import send_mail
from django.conf import settings
import requests, json
import sendgrid
import os
from sendgrid.helpers.mail import *

from apps.users.models import Code


def generate_code(size=6, chars=string.digits + string.ascii_letters):
    return ''.join(random.choice(chars) for x in range(size))


def send_email_code(email):
    code = generate_code(4)
    subject = 'Mentos User registration verification'
    html_message = '<p>尊敬的用户您好：<p>' \
                   '<p>您的验证码为：%s<p>' % (code)
    ret = False

    if settings.EMAIL_METHOD == 'sendgrid':
        send_success = send_via_api(email, subject, html_message)
    else:
        send_success = send_mail(subject, "", settings.EMAIL_FROM, [email], html_message=html_message)
    if send_success:
        time_now = time.time()
        time_now = int(time_now)
        Code.objects.create(email=email, code=code, create_time=time_now)
        ret = True
    else:
        ret = False
    return ret


def send_via_api(email, subject, html_message):
    sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    from_email = Email("test@example.com")
    to_email = To(email)
    subject = subject
    content = HtmlContent(html_message)
    mail = Mail(from_email, to_email, subject, content)
    print(mail.get())
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)
    return response.status_code == 200
