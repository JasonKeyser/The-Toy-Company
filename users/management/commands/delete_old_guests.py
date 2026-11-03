"""Delete guest accounts (and their games) that haven't been used in a while.

Usage:  python manage.py delete_old_guests            # older than 30 days
        python manage.py delete_old_guests --days 60
        python manage.py delete_old_guests --dry-run  # just count them
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone


class Command(BaseCommand):
    help = "Delete guest accounts that have been inactive for a number of days."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options["days"])
        old_guests = User.objects.filter(profile__is_guest=True).filter(
            Q(last_login__lt=cutoff) | Q(last_login__isnull=True, date_joined__lt=cutoff)
        )
        count = old_guests.count()
        if options["dry_run"]:
            self.stdout.write(f"{count} guest account(s) would be deleted.")
            return
        old_guests.delete()        # cascades to their Profile, Players, Turns, etc.
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} guest account(s)."))