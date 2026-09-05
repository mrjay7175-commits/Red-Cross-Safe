from django.db import migrations


def update_role_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    Branch = apps.get_model("Hospital", "Branch")
    Ambulance = apps.get_model("Hospital", "Ambulance")
    Vaccination = apps.get_model("Hospital", "Vaccination")
    InsuranceClaim = apps.get_model("Hospital", "InsuranceClaim")

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

    additions = {
        "Admin": [
            (Branch, ALL), (Ambulance, ALL), (Vaccination, ALL), (InsuranceClaim, ALL),
        ],
        "Doctor": [
            (Branch, RO), (Vaccination, RW), (InsuranceClaim, RO),
        ],
        "Receptionist": [
            (Branch, RO), (Ambulance, RW), (Vaccination, RO), (InsuranceClaim, RW),
        ],
        "Pharmacist": [
            (Branch, RO),
        ],
        "Lab Technician": [
            (Branch, RO), (Vaccination, RO),
        ],
    }

    for role, model_actions in additions.items():
        try:
            group = Group.objects.get(name=role)
        except Group.DoesNotExist:
            continue

        new_perms = []
        for model, actions in model_actions:
            new_perms.extend(perms_for(model, actions))

        for perm in new_perms:
            group.permissions.add(perm)


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("Hospital", "0008_branch_patient_email_ambulance_doctor_branch_and_more"),
    ]

    operations = [
        migrations.RunPython(update_role_permissions, reverse),
    ]
