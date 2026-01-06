from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from users.models import CustomUser


class Subscriber(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email", help_text="Введите почту")
    full_name = models.CharField(max_length=255, verbose_name="Ф.И.О.", help_text="Введите Ф.И.О.")
    comment = models.TextField(verbose_name="Комментарий", blank=True, null=True, help_text="Добавьте комментарий")
    owner = models.ForeignKey(
        CustomUser,
        verbose_name="Владелец",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class Message(models.Model):
    subject = models.CharField(max_length=255, verbose_name="Тема письма", help_text="Введите тему")
    body = models.TextField(verbose_name="Тело письма", help_text="Введите текст сообщения")
    owner = models.ForeignKey(
        CustomUser,
        verbose_name="Владелец",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "Письмо"
        verbose_name_plural = "Письма"

    def __str__(self):
        return self.subject


class MailingModel(models.Model):
    CREATED = "created"
    STARTED = "started"
    FINISHED = "finished"

    STATUSES_CHOICES = [
        (CREATED, "Создана"),
        (STARTED, "Запущена"),
        (FINISHED, "Завершена"),
    ]

    beginning_sending = models.DateTimeField(
        verbose_name="Начало рассылки",
        help_text="Укажите время в формате ДД.ММ.ГГГГ ЧЧ:ММ:СС",
    )
    end_sending = models.DateTimeField(
        verbose_name="Конец рассылки",
        help_text="Укажите время в формате ДД.ММ.ГГГГ ЧЧ:ММ:СС",
    )

    status = models.CharField(max_length=20, choices=STATUSES_CHOICES, default=CREATED, verbose_name="Статус")

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name="Сообщение",
        related_name="mailings",   # было messages
    )

    subscriber = models.ManyToManyField(
        Subscriber,
        verbose_name="Получатель рассылки",
        related_name="mailings",   # было subscribers
        help_text="Удерживайте “Control“ (или “Command“ на Mac), чтобы выбрать несколько значений.",
    )

    is_active = models.BooleanField(verbose_name="Активна", default=True)

    owner = models.ForeignKey(
        CustomUser,
        verbose_name="Владелец",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["beginning_sending"]
        permissions = [
            ("can_disable_mailing", "Can disable mailing"),
            ("can_send_message", "Can send_message"),
        ]

    def clean(self):
        now = timezone.now()
        if self.beginning_sending < now:
            raise ValidationError({"beginning_sending": "Начало рассылки не может быть в прошлом."})
        if self.beginning_sending >= self.end_sending:
            raise ValidationError({"end_sending": "Конец рассылки должен быть позже начала."})

    @property
    def calculated_status(self) -> str:
        now = timezone.now()
        if now < self.beginning_sending:
            return self.CREATED
        if self.beginning_sending <= now <= self.end_sending:
            return self.STARTED
        return self.FINISHED

    def save(self, *args, **kwargs):
        # чтобы статус не “зависал” неправильным
        self.status = self.calculated_status
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Рассылка #{self.pk} - {dict(self.STATUSES_CHOICES).get(self.status, self.status)}"


class MailingAttempt(models.Model):
    """Модель попытка рассылки"""

    SUCCESSFULLY = "successfully"
    NOT_SUCCESSFULL = "not_successful"

    STATUSES_CHOICES = [
        (SUCCESSFULLY, "Успешно"),
        (NOT_SUCCESSFULL, "Не успешно"),
    ]

    date_and_time = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")
    status = models.CharField(max_length=20, choices=STATUSES_CHOICES, verbose_name="Статус отправки")
    server_mail_response = models.TextField(verbose_name="Ответ почтового сервера", blank=True)

    mailing = models.ForeignKey(
        MailingModel,
        on_delete=models.CASCADE,
        related_name="attempts",   # было mailings
        verbose_name="Рассылка",
    )

    subscriber = models.ForeignKey(
        Subscriber,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Получатель",
    )

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"
        ordering = ["-date_and_time"]

    def __str__(self):
        return f"{self.date_and_time} - {self.get_status_display()}"
