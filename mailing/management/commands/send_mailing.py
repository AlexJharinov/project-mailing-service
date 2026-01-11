from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from mailing.models import MailingModel, MailingAttempt


class Command(BaseCommand):
    help = "Отправить рассылку вручную по ID через командную строку"

    def add_arguments(self, parser):
        parser.add_argument("pk", type=int, help="ID рассылки")

    def handle(self, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            mailing = MailingModel.objects.get(pk=pk)
        except MailingModel.DoesNotExist as exc:
            raise CommandError("Рассылка не найдена.") from exc

        now = timezone.now()

        # Проверки по ТЗ
        if now < mailing.beginning_sending or now > mailing.end_sending:
            raise CommandError("Нельзя отправлять рассылку вне окна start/end.")
        if not mailing.is_active:
            raise CommandError("Рассылка деактивирована.")
        if mailing.status == MailingModel.FINISHED:
            raise CommandError("Рассылка завершена. Отправка невозможна.")

        recipients = list(mailing.subscriber.values_list("email", flat=True))
        if not recipients:
            self.stdout.write(self.style.WARNING("У рассылки нет получателей."))
            return

        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
                recipient_list=recipients,
                fail_silently=False,
            )
            status_attempt = MailingAttempt.SUCCESSFULLY
            response = f"Отправлено писем: {len(recipients)}"
            self.stdout.write(self.style.SUCCESS(response))
        except Exception as e:
            status_attempt = MailingAttempt.NOT_SUCCESSFULL
            response = str(e)
            self.stdout.write(self.style.ERROR(f"Ошибка отправки: {response}"))

        # status рассылки лучше не хранить как факт отправки, но если у тебя так принято:
        mailing.status = MailingModel.STARTED
        mailing.save(update_fields=["status"])

        # date_and_time не передаём, если в модели auto_now_add=True
        MailingAttempt.objects.create(
            status=status_attempt,
            server_mail_response=response,
            mailing=mailing,
        )
