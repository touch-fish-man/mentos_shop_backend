import random
import string
import time

from django.core.mail import send_mail
from django.conf import settings

from apps.users.models import Code


def generate_code(size=6, chars=string.digits + string.ascii_letters):
    return ''.join(random.choice(chars) for x in range(size))


def send_email_code(email):
    code = generate_code(4)
    subject = '用户注册验证'
    html_message = '<p>尊敬的用户您好：<p>' \
                   '<p>您的验证码为：%s<p>' % (code)
    ret = False
    send_success = send_mail(subject, "", settings.EMAIL_FROM, [email], html_message=html_message)
    if send_success:
        time_now = time.time()
        time_now = int(time_now)
        Code.objects.create(email=email, code=code, create_time=time_now)
        ret = True
    else:
        ret = False
    return ret
