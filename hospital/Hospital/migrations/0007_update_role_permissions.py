from django.db import migrations


def update_role_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    LabTest = apps.get_model("Hospital", "LabTest")
    Ward = apps.get_model("Hospital", "Ward")
    Bed = apps.get_model("Hospital", "Bed")
    AuditLog = apps.get_model("Hospital", "AuditLog")

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
            (LabTest, ALL), (Ward, ALL), (Bed, ALL), (AuditLog, ALL),
        ],
        "Doctor": [
            (LabTest, RW), (Ward, RO), (Bed, RO),
        ],
        "Receptionist": [
            (Ward, RO), (Bed, RW),
        ],
        "Pharmacist": [],
        "Lab Technician": [
            (LabTest, RW), (Ward, RO), (Bed, RO),
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
        ("Hospital", "0006_ward_bill_payment_status_bill_razorpay_order_id_and_more"),
    ]

    operations = [
        migrations.RunPython(update_role_permissions, reverse),
    ]
