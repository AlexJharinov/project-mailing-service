from django.forms import ModelForm, BooleanField
from mailing.models import Subscriber, Message, MailingModel
from django.core.exceptions import ValidationError
from django.utils import timezone


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            css_class = 'form-check-input' if isinstance(field, BooleanField) else 'form-control'
            field.widget.attrs['class'] = css_class


class SubscriberForm(StyleFormMixin, ModelForm):
    class Meta:
        model = Subscriber
        exclude = ["owner"]


class MessageForm(StyleFormMixin, ModelForm):
    class Meta:
        model = Message
        exclude = ["owner"]


class MailingModelForm(StyleFormMixin, ModelForm):

    class Meta:
        model = MailingModel
        fields = ['beginning_sending', 'end_sending', 'status', 'message', 'subscriber']

    def clean(self):
        cleaned_data = super().clean()
        beginning_sending = cleaned_data.get('beginning_sending')
        end_sending = cleaned_data.get('end_sending')

        if beginning_sending and end_sending:
            if beginning_sending > end_sending:
                raise ValidationError("Начало рассылки не может быть позже окончания рассылки.")
            if end_sending < timezone.now():
                raise ValidationError("Окончание рассылки не может быть в прошлом.")
        return cleaned_data
