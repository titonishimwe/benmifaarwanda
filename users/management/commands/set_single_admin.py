from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Ensure only one admin user (staff + superuser). Demote others and optionally delete demo staff accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="tite",
            help="Username that should be the only admin (default: tite).",
        )
        parser.add_argument(
            "--delete",
            nargs="*",
            default=["admin", "smoke_admin"],
            help="Extra staff/demo usernames to delete (default: admin smoke_admin).",
        )
        parser.add_argument(
            "--demote",
            nargs="*",
            default=["tito"],
            help="Usernames to keep as members but remove staff/superuser (default: tito).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        admin_username = options["username"]
        admin = User.objects.filter(username=admin_username).first()
        if not admin:
            raise CommandError(f'User "{admin_username}" does not exist.')

        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.save(update_fields=["is_staff", "is_superuser", "is_active"])

        demote_names = [u for u in options["demote"] if u != admin_username]
        if demote_names:
            User.objects.filter(username__in=demote_names).update(
                is_staff=False, is_superuser=False
            )

        delete_names = [u for u in options["delete"] if u != admin_username]
        deleted_count = 0
        if delete_names:
            deleted_count, _ = User.objects.filter(username__in=delete_names).delete()

        User.objects.exclude(username=admin_username).update(is_superuser=False)
        User.objects.filter(username=admin_username).update(
            is_staff=True, is_superuser=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'"{admin_username}" is now the only admin (staff + superuser).'
            )
        )
        if demote_names:
            self.stdout.write(f"Demoted: {', '.join(demote_names)}")
        if delete_names:
            self.stdout.write(f"Deleted: {', '.join(delete_names)} ({deleted_count} rows)")

        remaining = User.objects.filter(is_staff=True).values_list("username", flat=True)
        self.stdout.write(f"Staff users now: {', '.join(remaining) or '(none)'}")
