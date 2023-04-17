import datetime
import random
import string
import time
import os

import pytz
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.core.mail import send_mail
from django.conf import settings
import requests
import json
import sendgrid
import os

from apps.users.models import Code, InviteLog, User
from apps.core.validators import CustomValidationError


def generate_code(size=6, chars=string.digits):
    return ''.join(random.choice(chars) for x in range(size))


def check_email_code(email, email_code_id, email_code, delete=False):
    code_item = Code.objects.filter(id=email_code_id, email=email, code=email_code)
    if settings.DEBUG:
        return code_item.first()
    if code_item.exists():
        db_code = code_item.first()
        # if db_code.create_time + settings.EMAIL_CODE_EXPIRE < datetime.datetime.now():
        if db_code.created_at + datetime.timedelta(minutes=settings.EMAIL_CODE_EXPIRE) < datetime.datetime.now().replace(tzinfo=pytz.timezone('UTC')):
            raise CustomValidationError("验证码已过期")
        if db_code.code.lower() == email_code.lower() or settings.DEBUG:
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
        db_code = code_item.first()
        if db_code.created_at + datetime.timedelta(minutes=10) < datetime.datetime.now():
            return False
        db_code.delete()
        return True
    else:
        return False


def send_email_code(email, email_template):
    code = generate_code(4)
    email_template=settings.EMAIL_TEMPLATES.get(email_template)
    subject = email_template.get('subject')
    html_message = email_template.get('html').replace('{{code}}', code).replace("{{expire_time}}",str(
                                                                                int(settings.EMAIL_CODE_EXPIRE / 60)))
    from_email = email_template.get('from_email')
    if settings.EMAIL_METHOD == 'sendgrid':
        send_success = send_via_sendgrid(email, subject, from_email, html_message)
    elif settings.EMAIL_METHOD == 'mailgun':
        send_success = send_email_via_mailgun(email, subject, from_email, html_message)
    else:
        send_success = send_mail(subject, "", from_email, [email], html_message=html_message)
    if send_success:
        code_obj = Code.objects.create(email=email, code=code)
        code_obj.save()
        code_id = code_obj.id
        ret = code_id
    else:
        ret = None
    return ret


def send_email_via_mailgun(email, subject, from_email, html_message):
    url = "https://api.mailgun.net/v3/{}/messages".format(settings.MAILGUN_SENDER_DOMAIN)
    post_data = {
        "from": from_email,
        "to": [email],
        "subject": subject,
        "html": html_message
    }

    resp = requests.post(url,
                         auth=("api", settings.MAILGUN_API_KEY),
                         data=post_data)
    return resp.status_code == 200


def send_via_sendgrid(email, subject, from_email, html_message):
    message = Mail(
        from_email=from_email,
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


def check_invite_code(invite_code):
    # 检查邀请码是否有效
    invite_code_obj = User.objects.filter(invite_code=invite_code).first()
    if invite_code_obj:
        return True
    else:
        return False


def insert_invite_log(uid, invite_code):
    # 查询邀请人
    user_obj = User.objects.filter(invite_code=invite_code).first()
    if user_obj:
        # 记录邀请日志
        InviteLog.objects.create(uid=uid, invite_code=invite_code, inviter_uid=user_obj.id)
        # 更新邀请计数
        user_obj.invite_count=user_obj.invite_count + 1
        # 更新邀请人等级积分
        user_obj.level_points=user_obj.level_points + settings.INVITE_LEVEL_POINTS_PER_USER
        user_obj.save()
        return True
    else:
        return False