from datetime import date, timedelta

from .models import Medicine, LabTest, Vaccination, Notification


def generate_alerts():
    """
    Scans for conditions worth notifying staff about and creates a
    Notification row per condition, using dedupe_key so re-running this
    (e.g. every few minutes, or nightly via cron) never creates duplicates
    for something already flagged.

    Returns the number of NEW notifications created.
    """

    created_count = 0

    from django.db.models import F

    # ---- Low stock medicines ----
    low_stock = Medicine.objects.filter(quantity__lte=F("reorder_level"))
    for med in low_stock:
        _, was_created = Notification.objects.get_or_create(
            dedupe_key=f"low_stock_{med.id}",
            defaults={
                "message": f"{med.name} is low on stock ({med.quantity} left, reorder at {med.reorder_level}).",
                "level": "warning",
                "link_name": "medicine_list",
            },
        )
        if was_created:
            created_count += 1

    # ---- Expiring medicines (within 30 days) ----
    soon = date.today() + timedelta(days=30)
    expiring = Medicine.objects.filter(expiry_date__gte=date.today(), expiry_date__lte=soon)
    for med in expiring:
        _, was_created = Notification.objects.get_or_create(
            dedupe_key=f"expiring_{med.id}_{med.expiry_date}",
            defaults={
                "message": f"{med.name} expires on {med.expiry_date} - plan to use or replace stock.",
                "level": "warning",
                "link_name": "medicine_list",
            },
        )
        if was_created:
            created_count += 1

    # ---- Lab tests pending for more than 3 days ----
    stale_cutoff = date.today() - timedelta(days=3)
    stale_tests = LabTest.objects.filter(status="Pending", test_date__date__lte=stale_cutoff)
    for test in stale_tests:
        _, was_created = Notification.objects.get_or_create(
            dedupe_key=f"stale_labtest_{test.id}",
            defaults={
                "message": f"Lab test '{test.test_name}' for {test.patient.name} has been pending for 3+ days.",
                "level": "danger",
                "link_name": "lab_test_list",
            },
        )
        if was_created:
            created_count += 1

    # ---- Vaccinations due within the next 7 days ----
    due_soon = date.today() + timedelta(days=7)
    due_vaccinations = Vaccination.objects.filter(
        next_due_date__isnull=False,
        next_due_date__gte=date.today(),
        next_due_date__lte=due_soon,
    )
    for vac in due_vaccinations:
        _, was_created = Notification.objects.get_or_create(
            dedupe_key=f"vaccine_due_{vac.id}_{vac.next_due_date}",
            defaults={
                "message": f"{vac.patient.name} has a {vac.vaccine_name} dose due on {vac.next_due_date}.",
                "level": "info",
                "link_name": "vaccination_list",
            },
        )
        if was_created:
            created_count += 1

    return created_count
