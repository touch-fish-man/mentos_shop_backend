import os
if os.environ.get('DJANGO_ENV') == 'prod':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.production")
elif os.environ.get('DJANGO_ENV') == 'local':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
elif os.environ.get('DJANGO_ENV') == 'test':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.test")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")

from users import main as mock_users
from tickets import main as mock_tickets
from acls import main as mock_acls
from proxy import main as mock_proxy
from servers import main as mock_servers

mock_users()
mock_tickets()
mock_acls()
mock_proxy()
mock_servers()



