"""
ASGI config for gourmet_proj project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

# pyright: reportMissingImports=false, reportMissingModuleSource=false
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gourmet_proj.settings')

application = get_asgi_application()
