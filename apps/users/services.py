import datetime
import random
import string
import time
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.core.mail import send_mail
from django.conf import settings
import requests, json
import sendgrid
import os
# from sendgrid.helpers.mail import *

from apps.users.models import Code
from apps.core.validators import CustomValidationError


def generate_code(size=6, chars=string.digits + string.ascii_letters):
    return ''.join(random.choice(chars) for x in range(size))


def check_email_code(email, email_code_id, email_code, delete=False):
    code_item = Code.objects.filter(id=email_code_id, email=email, code=email_code)
    if code_item.exists():
        db_code = code_item.order_by('-create_time').first()
        if db_code.create_time + datetime.timedelta(minutes=5) < datetime.datetime.now():
            raise CustomValidationError("验证码已过期")
        if db_code.code.lower() == email_code.lower():
            if delete:
                db_code.delete()
            else:
                return db_code
            return True
        else:
            raise CustomValidationError("验证码错误")
    else:
        raise CustomValidationError("验证码错误")


def check_verify_id(email, verify_id):
    code_item = Code.objects.filter(email=email, verify_id=verify_id)
    if code_item.exists():
        db_code = code_item.order_by('-create_time').first()
        if db_code.create_time + datetime.timedelta(minutes=10) < datetime.datetime.now():
            return False
        db_code.delete()
        return True
    else:
        return False


def send_email_code(email):
    code = generate_code(4)
    subject = 'Mentos User registration verification'
    html_message = '<p>尊敬的用户您好：<p>' \
                   '<p>您的验证码为：%s<p>' % (code)
    if settings.EMAIL_METHOD == 'sendgrid':
        send_success = send_via_api(email, subject, html_message)
    else:
        send_success = send_mail(subject, "", settings.EMAIL_FROM, [email], html_message=html_message)
    if send_success:
        time_now = time.time()
        time_now = int(time_now)
        code_obj = Code.objects.create(email=email, code=code, create_time=time_now)
        code_obj.save()
        code_id = code_obj.id
        ret = code_id
    else:
        ret = None
    return ret


def send_via_api(email, subject, html_message):
    message = Mail(
        from_email='mentos@run-run.run',
        to_emails=email,
        subject=subject,
        html_content=html_message)
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code == 202:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False

    # sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    # from_email = Email("test@example.com")
    # to_email = To(email)
    # subject = subject
    # content = HtmlContent(html_message)
    # mail = Mail(from_email, to_email, subject, content)
    # print(mail.get())
    # response = sg.client.mail.send.post(request_body=mail.get())
    # print(response.status_code)
    # print(response.body)
    # print(response.headers)
    # return response.status_code == 200
