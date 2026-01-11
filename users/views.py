import secrets
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView, ListView
from users.forms import CustomUserCreationForm, UserUpdateForm
from users.models import CustomUser
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group


# новая версия с добавлением в группу владельца при создании
class RegisterView(CreateView):
    template_name = "users/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.is_active = False
        self.object.token = secrets.token_hex(16)
        self.object.save()
        form.save_m2m()

        owners_group, _ = Group.objects.get_or_create(name="Owners")
        self.object.groups.add(owners_group)

        host = self.request.get_host()
        url = f"http://{host}/users/email-confirm/{self.object.token}/"

        try:
            send_mail(
                subject="Добро пожаловать в наш сервис!",
                message=(
                    "Спасибо, что зарегистрировались! "
                    f"Перейдите по ссылке для подтверждения почты: {url}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,  # лучше так, чем EMAIL_HOST_USER
                recipient_list=[self.object.email],
                fail_silently=False,
            )
            messages.success(self.request, "Письмо с подтверждением отправлено на вашу почту.")
        except Exception:
            # Можно оставить так, чтобы не валить регистрацию
            messages.warning(self.request, "Не удалось отправить письмо подтверждения. Попробуйте позже.")

        return super().form_valid(form)


def email_verification(request, token):
    '''
    Функция получает токен после перехода пользователя по ссылке, отправленной методом form_valid
    и сравнивает его с токеном в базе этого пользователя, если они совпадают, то меняет статус
    пользователя на активный.
    '''

    user = get_object_or_404(CustomUser, token=token)
    user.is_active = True
    user.save()
    return redirect(reverse('users:login'))


class ProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/profile.html'
    context_object_name = 'user'

    def get_object(self, queryset=None):
        return self.request.user  # Возвращается текущий пользователь


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserUpdateForm
    template_name = 'users/edit_profile.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user  # Возвращается обновленный текущий пользователь


class ProfileListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/profile_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        user = self.request.user
        if user.has_perm('users.view_customuser'):
            return (CustomUser.objects.filter(is_active=True)
                                      .exclude(is_superuser=True)
                                      .exclude(id=self.request.user.id))


# class ProfileListView(LoginRequiredMixin, ListView):
#     model = CustomUser
#     template_name = 'users/profile_list.html'
#     context_object_name = 'users'
#
#     def get(self, request, *args, **kwargs):
#         user = request.user
#         if not (user.is_superuser or user.groups.filter(name='Managers').exists()):
#             messages.warning(request, 'У вас нет доступа!')
#             return redirect('mailing:home')
#         return super().get(request, *args, **kwargs)
#
#     def get_queryset(self):
#         return CustomUser.objects.filter(is_active=True).exclude(is_superuser=True).exclude(id=self.request.user.id)


class DisableProfileView(LoginRequiredMixin, View):
    def get(self, request, pk):
        # Получаем объект профиля
        profile = get_object_or_404(CustomUser, pk=pk)
        # Формируем и отправляем страницу подтверждения
        return render(request, 'users/confirm_disable_profile.html', {'profile': profile})

    def post(self, request, pk):
        user = self.request.user
        # Получаем объект модели
        profile = get_object_or_404(CustomUser, pk=pk)
        # Получаем группу "менеджеры"
        if user.has_perm('users.can_deactivate_user'):
            # Если пользователь обладает правом деактивации пользователя
            profile.is_active = False
            profile.save()
            # Подтверждение успешной операции
            messages.success(request, "Профиль успешно деактивирован!")
        else:
            # Иначе сообщаем об ошибке
            messages.warning(request, "У вас нет прав отключить рассылку.")
        return redirect('users:profile_list')

# Create your views here.
