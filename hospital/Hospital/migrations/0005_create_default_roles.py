from django.db import migrations


def create_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    Patient = apps.get_model("Hospital", "Patient")
    Doctor = apps.get_model("Hospital", "Doctor")
    Bill = apps.get_model("Hospital", "Bill")
    Medicine = apps.get_model("Hospital", "Medicine")
    Appointment = apps.get_model("Hospital", "Appointment")
    MedicalRecord = apps.get_model("Hospital", "MedicalRecord")
    NotificationSettings = apps.get_model("Hospital", "NotificationSettings")

    ALL = ["add", "change", "delete", "view"]
    RW = ["add", "change", "view"]
    RO = ["view"]

    def perms_for(model, actions):
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

    for role, model_actions in role_perms.items():
        group, _ = Group.objects.get_or_create(name=role)
        all_perms = []
        for model, actions in model_actions:
            all_perms.extend(perms_for(model, actions))
        group.permissions.set(all_perms)


def reverse(apps, schema_editor):
    # Leave groups in place on reverse migration; deleting them could
    # remove role assignments the admin has manually configured.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("Hospital", "0004_medicalrecord"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_roles, reverse),
    ]
