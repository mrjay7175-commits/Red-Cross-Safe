from django.core.management.base import BaseCommand
from Hospital.alerts import generate_alerts


class Command(BaseCommand):
    help = (
        "Scans for low stock / expiring medicines, stale pending lab tests, "
        "and upcoming vaccination due dates, and creates in-app notifications "
        "for staff. Safe to run repeatedly - it won't create duplicates. "
        "Schedule this every 15-30 minutes via cron/Task Scheduler for "
        "near-real-time alerts (see DEPLOYMENT.md)."
    )

    def handle(self, *args, **options):
        count = generate_alerts()
        self.stdout.write(self.style.SUCCESS(f"Generated {count} new notification(s)."))
