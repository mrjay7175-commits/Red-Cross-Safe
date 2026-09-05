from django.apps import AppConfig


class HospitaldataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Hospital'

    def ready(self):
        from . import signals
        signals.connect_audit_signals()
