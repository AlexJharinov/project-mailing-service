from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = "Create default groups and assign permissions"

    def handle(self, *args, **kwargs):
        owners, _ = Group.objects.get_or_create(name="Owners")

        perms = Permission.objects.filter(codename__in=[
            # Subscriber
            "add_subscriber", "change_subscriber", "delete_subscriber", "view_subscriber",
            # Message
            "add_message", "change_message", "delete_message", "view_message",
            # MailingModel
            "add_mailingmodel", "change_mailingmodel", "delete_mailingmodel", "view_mailingmodel",
        ])
        owners.permissions.add(*perms)

        self.stdout.write(self.style.SUCCESS("Owners group created/updated"))
