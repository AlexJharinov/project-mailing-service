from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from mailing.models import MailingModel, MailingAttempt
from django.conf import settings
from django.utils import timezone


class Command(BaseCommand):
    help = 'Отправить рассылку вручную по ID через командную строку'

    # Задает аргумент для передачи в командную строку, когда запустим команду
    def add_arguments(self, parser):
        parser.add_argument('pk', type=int, help='ID рассылки')

    def handle(self, *args, **kwargs):
        pk = kwargs['pk']
        try:
            mailing = MailingModel.objects.get(pk=pk)
        except MailingModel.DoesNotExist:
            raise CommandError('Рассылка не найдена.')

        if mailing.status == MailingModel.FINISHED:
            self.stdout.write(self.style.ERROR('Рассылка завершена. Отправка невозможна.'))
            return

        subject = mailing.message.subject
        body = mailing.message.body
        subscriber = mailing.subscriber.all()
        emails = [p.email for p in subscriber]

        if not emails:
            self.stdout.write(self.style.WARNING('У рассылки нет получателей.'))
        for email in emails:
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
                mailing.status = MailingModel.STARTED
                mailing.save()

                status_mailing_attempt = MailingAttempt.SUCCESSFULLY
                server_mail_response = 'Письмо отправлено'

            except Exception as e:
                status_mailing_attempt = MailingAttempt.NOT_SUCCESSFULL
                server_mail_response = str(e)

            MailingAttempt.objects.create(
                date_and_time=timezone.now(),
                status=status_mailing_attempt,
                server_mail_response=server_mail_response,
                mailing=mailing
            )
        self.stdout.write(self.style.SUCCESS(f'Успешно отправлено писем: {len(emails)}.'))