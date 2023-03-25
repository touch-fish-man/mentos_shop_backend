"""
ASGI config for proxy_admin project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
if os.environ.get('DJANGO_ENV') == 'prod':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.production")
elif os.environ.get('DJANGO_ENV') == 'local':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
elif os.environ.get('DJANGO_ENV') == 'test':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.test")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.production")

application = get_asgi_application()
