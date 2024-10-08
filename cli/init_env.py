import os
import sys

import django
if os.environ.get('DJANGO_ENV'):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists(os.path.join(base_dir, 'config', 'django', os.environ.get('DJANGO_ENV') + '.py')):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django." + os.environ.get('DJANGO_ENV'))
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.prod")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.prod")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



django.setup()
