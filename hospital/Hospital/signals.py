from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .middleware import get_current_user
from .models import (
    Patient,
    Doctor,
    Bill,
    Medicine,
    Appointment,
    MedicalRecord,
    LabTest,
    Ward,
    Bed,
    AuditLog,
    Branch,
    Ambulance,
    Vaccination,
    InsuranceClaim,
)

AUDITED_MODELS = [
    Patient, Doctor, Bill, Medicine, Appointment,
    MedicalRecord, LabTest, Ward, Bed,
    Branch, Ambulance, Vaccination, InsuranceClaim,
]


def _current_user_or_none():
    user = get_current_user()
    if user is not None and getattr(user, "is_authenticated", False):
        return user
    return None


def _log(action, instance):
    # Never let audit logging break the actual request/operation.
    try:
        AuditLog.objects.create(
            user=_current_user_or_none(),
            action=action,
            model_name=instance.__class__.__name__,
            object_repr=str(instance)[:255],
        )
    except Exception:
        pass

    # Dashboard stats are cached briefly for performance (see
    # dashboard_stats_json) - clear it so changes show up immediately
    # instead of waiting out the cache timeout.
    try:
        cache.delete("dashboard_stats")
    except Exception:
        pass


def make_save_handler():
    def handler(sender, instance, created, **kwargs):
        _log("Created" if created else "Updated", instance)
    return handler


def make_delete_handler():
    def handler(sender, instance, **kwargs):
        _log("Deleted", instance)
    return handler


def connect_audit_signals():
    save_handler = make_save_handler()
    delete_handler = make_delete_handler()

    for model in AUDITED_MODELS:
        post_save.connect(save_handler, sender=model, weak=False)
        post_delete.connect(delete_handler, sender=model, weak=False)
