#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    print("manage.py")
    print(os.environ.get('DJANGO_ENV'))
    if os.environ.get('DJANGO_ENV'):
        if os.path.exists(os.path.join(os.getcwd(), 'config', 'django', os.environ.get('DJANGO_ENV') + '.py')):
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django." + os.environ.get('DJANGO_ENV'))
        else:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
