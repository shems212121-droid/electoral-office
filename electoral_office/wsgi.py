"""
WSGI config for electoral_office project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Force production settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings_production')

application = get_wsgi_application()
