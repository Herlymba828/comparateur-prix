from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

"""
Management command: init_roles

Ensures role groups exist and (optionally) attaches a baseline set of Django model
permissions. Idempotent and safe to run multiple times.

Groups created:
- admin
- moderateur
- user

Usage:
    python manage.py init_roles [--with-perms]
"""

BASELINE_PERMS = {
    # Example baseline permissions. Adjust to your needs.
    "admin": [
        ("auth", "user", ["add", "change", "delete", "view"]),
        ("sessions", "session", ["delete", "view"]),
    ],
    "moderateur": [
        ("auth", "user", ["change", "view"]),
    ],
    "user": [
        # No global model perms by default; access is enforced by app logic.
    ],
}

class Command(BaseCommand):
    help = "Initialize role groups: admin, moderateur, user (idempotent). Optionally attach baseline permissions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-perms",
            action="store_true",
            help="Attach a baseline set of Django model permissions to groups",
        )

    def handle(self, *args, **options):
        created = []
        for group_name in ["admin", "moderateur", "user"]:
            grp, was_created = Group.objects.get_or_create(name=group_name)
            if was_created:
                created.append(group_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created groups: {', '.join(created)}"))
        else:
            self.stdout.write("Groups already exist (no changes)")

        if options.get("with_perms"):
            attached = []
            for group_name, entries in BASELINE_PERMS.items():
                grp = Group.objects.get(name=group_name)
                for app_label, model, actions in entries:
                    try:
                        ct = ContentType.objects.get(app_label=app_label, model=model)
                    except ContentType.DoesNotExist:
                        # Skip if content type not present in this project
                        continue
                    for action in actions:
                        codename = f"{action}_{model}"
                        try:
                            perm = Permission.objects.get(content_type=ct, codename=codename)
                            grp.permissions.add(perm)
                            attached.append(f"{group_name}:{codename}")
                        except Permission.DoesNotExist:
                            # Skip silently if permission doesn't exist
                            continue
            if attached:
                self.stdout.write(self.style.SUCCESS(f"Attached permissions: {', '.join(attached)}"))
            else:
                self.stdout.write("No permissions attached (none found or already present)")

        self.stdout.write(self.style.SUCCESS("Role initialization complete."))
