from PIL import Image
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser
from mailing.forms import StyleFormMixin


class CustomUserCreationForm(StyleFormMixin, UserCreationForm):

    usable_password = None  # позволяет убрать из формы UserCreationForm Password-based authentication

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'country', 'phone_number', 'avatar', 'password1', 'password2',]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].help_text = 'Обязательно'
        self.fields['username'].help_text = 'Обязательно'
        self.fields['username'].label = 'Пользователь'
        self.fields['phone_number'].label = 'Телефон'

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and not phone_number.isdigit():
            raise forms.ValidationError('Номер телефона должен состоять только из цифр')
        return phone_number

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')

        if avatar:
            # Проверка размера
            max_size_mb = 5
            if avatar.size > max_size_mb * 1024 * 1024:
                raise ValidationError(f"Размер изображения не должен превышать {max_size_mb} МБ.")

            # открываем загруженный файл как изображение
            img = Image.open(avatar)
            # возвращаем реальный формат изображения
            img_format = img.format  # Например: 'JPEG', 'PNG', 'GIF', 'BMP' и т.д.
            # проверяем соответствует ли формат 'JPEG', 'PNG', если нет, то вызываем исключение
            if img_format not in ['JPEG', 'PNG']:
                raise ValidationError("Допустимы только форматы JPEG или PNG.")
        return avatar


class UserUpdateForm(forms.ModelForm):
    class Meta(CustomUserCreationForm.Meta):
        fields = ['email', 'username', 'country', 'phone_number', 'avatar',]