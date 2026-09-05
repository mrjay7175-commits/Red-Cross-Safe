import shutil
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = (
        "Creates a timestamped backup of the database (and, for SQLite, "
        "copies the .sqlite3 file directly). Intended to be run on a "
        "schedule (cron / Windows Task Scheduler) for automatic backups - "
        "see DEPLOYMENT.md for how to wire that up."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep",
            type=int,
            default=14,
            help="Number of most recent backups to keep (older ones are deleted). Default: 14.",
        )

    def handle(self, *args, **options):
        db_settings = settings.DATABASES["default"]
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if db_settings["ENGINE"] == "django.db.backends.sqlite3":
            src = Path(db_settings["NAME"])
            dest = backup_dir / f"db_backup_{timestamp}.sqlite3"
            shutil.copy(src, dest)
            self.stdout.write(self.style.SUCCESS(f"Backed up SQLite database to {dest}"))
        else:
            self.stdout.write(self.style.WARNING(
                "Non-SQLite database detected - use your database's native "
                "backup tool instead (e.g. pg_dump for Postgres, mysqldump "
                "for MySQL). This command only handles SQLite directly."
            ))
            return

        # Prune old backups beyond --keep
        keep = options["keep"]
        backups = sorted(backup_dir.glob("db_backup_*.sqlite3"), reverse=True)
        for old_backup in backups[keep:]:
            old_backup.unlink()
            self.stdout.write(f"Removed old backup: {old_backup.name}")
