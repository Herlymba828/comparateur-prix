from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

# This command initializes role groups used across the application:
# - admin
# - moderateur
# - premium
# It will create groups if missing and (optionally) attach a baseline set of permissions.
# You can run it safely multiple times; it is idempotent.

BASELINE_PERMS = {
    # Example: attach change/add/delete permissions on user to admin/moderator if desired
    # (You can customize to your needs later.)
    "admin": [
        ("auth", "user", ["add", "change", "delete", "view"]),
        ("sessions", "session", ["delete", "view"]),
    ],
    "moderateur": [
        ("auth", "user", ["change", "view"]),
    ],
    "premium": [
        # No global model perms by default; application logic checks IsPremium for premium-only features
    ],
}

class Command(BaseCommand):
    help = "Initialize role groups: admin, moderateur, premium (idempotent). Optionally attach baseline permissions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-perms",
            action="store_true",
            help="Attach a baseline set of Django model permissions to groups",
        )

    def handle(self, *args, **options):
        created = []
        for group_name in ["admin", "moderateur", "premium"]:
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
