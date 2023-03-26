"""
ASGI config for proxy_admin project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
if os.environ.get('DJANGO_ENV'):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists(os.path.join(base_dir, 'config', 'django', os.environ.get('DJANGO_ENV') + '.py')):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django." + os.environ.get('DJANGO_ENV'))
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")

application = get_asgi_application()
