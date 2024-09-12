import logging

import requests
from django.conf import settings
from django.core.mail import send_mail
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


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


def send_email_api(email, subject, from_email, html_message):
    if settings.EMAIL_METHOD == 'sendgrid':
        send_success = send_via_sendgrid(email, subject, from_email, html_message)
    elif settings.EMAIL_METHOD == 'mailgun':
        send_success = send_email_via_mailgun(email, subject, from_email, html_message)
    else:
        send_success = send_mail(subject, "", from_email, [email], html_message=html_message)
    logging.info("email send success: %s" % send_success)
    return send_success


class EmailSender:
    @classmethod
    def send_email(cls, email, data):
        tamplate_name = data['template']
        email_template = settings.EMAIL_TEMPLATES.get(tamplate_name)
        subject = email_template.get('subject')
        html_message = email_template.get('html')
        for key, value in data['data'].items():
            subject = subject.replace("{{" + key + "}}", value)
            html_message = html_message.replace("{{" + key + "}}", value)
        from_email = email_template.get('from_email')
        return send_email_api(email, subject, from_email, html_message)
