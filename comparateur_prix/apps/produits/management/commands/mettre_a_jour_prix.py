from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Alias français: lance la commande 'update_prices'"

    def add_arguments(self, parser):
        parser.add_argument("--supermarches", type=str)
        parser.add_argument("--hypermarches", type=str)
        parser.add_argument("--max-workers", type=int)

    def handle(self, *args, **options):
        cmd = ["update_prices"]
        if options.get("supermarches"):
            cmd.extend(["--supermarches", options["supermarches"]])
        if options.get("hypermarches"):
            cmd.extend(["--hypermarches", options["hypermarches"]])
        if options.get("max_workers") is not None:
            cmd.extend(["--max-workers", str(options["max_workers"])])
        call_command(*cmd)
