from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from Hospital.models import (
    Patient,
    Doctor,
    Bill,
    Medicine,
    Appointment,
    MedicalRecord,
    NotificationSettings,
)

try:
    from prescription.models import Prescription
except Exception:
    Prescription = None


def perms_for(model, actions):
    """Return Permission objects for the given actions (add/change/delete/view)
    on the given model, creating any that are missing."""
    ct = ContentType.objects.get_for_model(model)
    result = []
    for action in actions:
        codename = f"{action}_{model._meta.model_name}"
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=ct,
            defaults={"name": f"Can {action} {model._meta.verbose_name}"},
        )
        result.append(perm)
    return result


ALL = ["add", "change", "delete", "view"]
RW = ["add", "change", "view"]
RO = ["view"]


class Command(BaseCommand):
    help = "Create the standard hospital roles (groups) with sensible default permissions."

    def handle(self, *args, **options):

        role_perms = {
            "Admin": [
                (Patient, ALL), (Doctor, ALL), (Bill, ALL), (Medicine, ALL),
                (Appointment, ALL), (MedicalRecord, ALL), (NotificationSettings, ALL),
            ],
            "Doctor": [
                (Patient, RO), (Doctor, RO), (Bill, RO),
                (Appointment, RW), (MedicalRecord, RW), (Medicine, RO),
            ],
            "Receptionist": [
                (Patient, RW), (Doctor, RO), (Bill, RW), (Appointment, RW),
            ],
            "Pharmacist": [
                (Medicine, RW), (Patient, RO), (Bill, RO),
            ],
            "Lab Technician": [
                (Patient, RO), (MedicalRecord, RW),
            ],
        }

        if Prescription is not None:
            for role in ("Admin",):
                role_perms[role].append((Prescription, ALL))
            role_perms["Doctor"].append((Prescription, RW))
            role_perms["Receptionist"].append((Prescription, RO))

        for role, model_actions in role_perms.items():

            group, created = Group.objects.get_or_create(name=role)

            all_perms = []
            for model, actions in model_actions:
                all_perms.extend(perms_for(model, actions))

            group.permissions.set(all_perms)

            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{status} group '{role}' with {len(all_perms)} permissions"))

        self.stdout.write(self.style.SUCCESS("Done. Assign users to these groups via /register/ (role field) or Django admin."))
