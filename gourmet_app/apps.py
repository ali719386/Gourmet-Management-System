# pyright: reportMissingImports=false, reportMissingModuleSource=false
from django.apps import AppConfig


class GourmetAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gourmet_app'

def ready(self):
    import gourmet_app.signals
