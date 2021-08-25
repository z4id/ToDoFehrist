from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

import uuid


def send_email(subject, body, to_):

    new_email = EmailMessage(subject, body, to=to_)
    new_email.send()


def account_act_token_gen():
    return PasswordResetTokenGenerator()


def send_activation_email(app_user, request):
    subject = 'ToDoFehrist - Activate Your Account'
    body = render_to_string('email_verification.html', {
        "domain": get_current_site(request).domain,
        "uid": urlsafe_base64_encode(force_bytes(app_user.pk)),
        "token": account_act_token_gen().make_token(app_user)
    })

    send_email(subject, body, [app_user.email])
