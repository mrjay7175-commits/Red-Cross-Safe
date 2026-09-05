from django.db import migrations


def update_role_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    Notification = apps.get_model("Hospital", "Notification")

    ct = ContentType.objects.get_for_model(Notification)
    perms = []
    for action in ["add", "change", "delete", "view"]:
        codename = f"{action}_{Notification._meta.model_name}"
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=ct,
            defaults={"name": f"Can {action} {Notification._meta.verbose_name}"},
        )
        perms.append(perm)

    try:
        admin_group = Group.objects.get(name="Admin")
        for perm in perms:
            admin_group.permissions.add(perm)
    except Group.DoesNotExist:
        pass


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("Hospital", "0011_notification"),
    ]

    operations = [
        migrations.RunPython(update_role_permissions, reverse),
    ]
