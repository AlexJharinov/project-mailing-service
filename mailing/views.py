from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from mailing.forms import SubscriberForm, MessageForm, MailingModelForm
from mailing.models import Subscriber, Message, MailingModel, MailingAttempt
from django.conf import settings
from django.utils import timezone
from mailing.services import get_subscriber_list_from_cache, get_message_list_from_cache, get_mailing_list_from_cache
# from django.contrib.auth.models import Group


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "mailing/home.html"

    from django.utils import timezone

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()

        mailings = MailingModel.objects.filter(owner=user)

        context["total_mailings"] = mailings.count()

        context["active_mailings"] = mailings.filter(
            is_active=True,
            beginning_sending__lte=now,
            end_sending__gte=now,
        ).count()

        context["unique_subscribers"] = (
            mailings.values("subscriber").distinct().count()
        )

        return context

    # # если нужно всего в системе
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['total_mailings'] = MailingModel.objects.count()
    #     context['active_mailings'] = MailingModel.objects.filter(status=MailingModel.STARTED).count()
    #     context['unique_subscribers'] = Subscriber.objects.count()
    #     return context


class SubscriberListView(LoginRequiredMixin, ListView):
    '''Список получателей рассылки (подписчиков)'''
    model = Subscriber
    template_name = 'mailing/subscriber_list.html'  # можно не указывать, это стандартный путь
    context_object_name = 'subscriber_list'  # можно не указывать, если использовать это
    # стандартное название в шаблоне 'subscriber_list' или 'object_list'

    def get_queryset(self):
        user = self.request.user
        # Используем сервисную функцию и получаем список получателей рассылки из кеша.
        # Если кеш пуст, то сервисная функция получает данные из БД
        return get_subscriber_list_from_cache(user)

    # # Без кеширования
    # def get_queryset(self):
    #     user = self.request.user
    #     try:
    #         # Получаем группу Owners
    #         owners_group = Group.objects.get(name='Owners')
    #         # Проверяем, состоит ли пользователь в группе Owners
    #         if owners_group in user.groups.all():
    #             # Если пользователь в группе Owners, возвращаем только его подписчиков
    #             return Subscriber.objects.filter(owner=user)
    #         # Если пользователь не в группе Owners, проверяем наличие права на просмотр всех подписчиков
    #         elif user.has_perm('mailing.view_subscriber'):
    #             # Если у пользователя есть разрешение, возвращаем всех подписчиков
    #             return Subscriber.objects.all()
    #     except Group.DoesNotExist:
    #         # Если группа Owners не найдена, возвращаем пустой список
    #         return Subscriber.objects.none()
    #     # Если пользователь не попадает ни в одну категорию, возвращаем пустой список
    #     return Subscriber.objects.none()


@method_decorator(cache_page(20), name='dispatch')
class SubscriberDetailView(LoginRequiredMixin, DetailView):
    '''Детальная информация по получателю рассылки (подписчику)'''
    model = Subscriber
    template_name = 'mailing/subscriber_detail.html'  # можно не указывать, это стандартный путь
    context_object_name = 'subscriber'  # можно не указывать, стандартное название в шаблоне 'subscriber'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        # Если пользователь является владельцем объекта, видит свой объект
        if user == obj.owner:
            return obj
        # Если пользователь не владелец, проверяем наличие права на просмотр всех подписчиков
        elif user.has_perm('mailing.view_subscriber'):
            return obj
        # Если пользователь не владелец и не имеет права на просмотр, запрещаем доступ
        else:
            raise PermissionDenied("У Вас недостаточно прав для просмотра этого профиля.")


class SubscriberCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    '''Создание нового получателя рассылки (подписчика)'''
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'mailing/subscriber_form.html'
    success_url = reverse_lazy('mailing:subscriber_list')
    permission_required = 'mailing.add_subscriber'

    def form_valid(self, form):
        subscriber = form.save()
        user = self.request.user
        subscriber.owner = user
        subscriber.save()
        return super().form_valid(form)


class SubscriberUpdateView(LoginRequiredMixin, UpdateView):
    '''Обновление получателя рассылки (подписчика)'''
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'mailing/subscriber_form.html'
    context_object_name = 'subscriber'
    permission_required = 'mailing.change_subscriber'

    def get_success_url(self):
        return reverse_lazy('mailing:subscriber_detail', kwargs={'pk': self.object.pk})

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        # Если пользователь является владельцем объекта, допускаем доступ
        if user == obj.owner:
            return obj
        # Если пользователь не владелец, проверяем наличие права на изменение любых подписчиков
        elif user.has_perm('mailing.change_subscriber'):
            return obj
        # Если пользователь не владелец и не имеет права на изменение, запрещаем доступ
        else:
            raise PermissionDenied("У Вас недостаточно прав для изменения.")


class SubscriberDeleteView(LoginRequiredMixin, DeleteView):
    '''Удаление получателя рассылки (подписчика)'''
    model = Subscriber
    template_name = 'mailing/subscriber_confirm_delete.html'
    context_object_name = 'subscriber'
    success_url = reverse_lazy('mailing:subscriber_list')
    permission_required = 'mailing.delete_subscriber'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        # Если пользователь является владельцем объекта, допускаем доступ
        if user == obj.owner:
            return obj
        # Если пользователь не владелец, проверяем наличие права на изменение любых подписчиков
        elif user.has_perm('mailing.delete_subscriber'):
            return obj
        # Если пользователь не владелец и не имеет права на изменение, запрещаем доступ
        else:
            raise PermissionDenied("У Вас недостаточно прав для удаления.")


class MessageListView(LoginRequiredMixin, ListView):
    '''Список сообщений для рассылки'''
    model = Message
    template_name = 'mailing/message_list.html'
    context_object_name = 'message_list'

    def get_queryset(self):
        user = self.request.user
        # Используем сервисную функцию и получаем список сообщений из кеша.
        # Если кеш пуст, то сервисная функция получает данные из БД
        return get_message_list_from_cache(user)

    # # без кеширования
    # def get_queryset(self):
    #     user = self.request.user
    #     try:
    #         # Получаем группу Owners
    #         owners_group = Group.objects.get(name='Owners')
    #         # Проверяем, состоит ли пользователь в группе Owners
    #         if owners_group in user.groups.all():
    #             # Если пользователь в группе Owners, возвращаем только его сообщения
    #             return Message.objects.filter(owner=user)
    #         # Если пользователь не в группе Owners, проверяем наличие права на просмотр всех сообщений
    #         elif user.has_perm('mailing.view_message'):
    #             # Если у пользователя есть разрешение, возвращаем все сообщения
    #             return Message.objects.all()
    #     except Group.DoesNotExist:
    #         # Если группа Owners не найдена, возвращаем пустой список
    #         return Message.objects.none()
    #     # Если пользователь не попадает ни в одну категорию, возвращаем пустой список
    #     return Message.objects.none()


@method_decorator(cache_page(20), name='dispatch')
class MessageDetailView(LoginRequiredMixin, DetailView):
    '''Детальная информация о сообщении'''
    model = Message
    template_name = 'mailing/message_detail.html'
    context_object_name = 'message'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        # Если пользователь является владельцем объекта, видит свой объект
        if user == obj.owner:
            return obj
        # Если пользователь не владелец, проверяем наличие права на просмотр всех подписчиков
        elif user.has_perm('mailing.view_message'):
            return obj
        # Если пользователь не владелец и не имеет права на просмотр, запрещаем доступ
        else:
            raise PermissionDenied("У Вас недостаточно прав для просмотра.")


class MessageCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    '''Создание нового сообщения'''
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')
    permission_required = 'mailing.add_message'

    def form_valid(self, form):
        message = form.save()
        user = self.request.user
        message.owner = user
        message.save()
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    '''Изменение сообщения'''
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    context_object_name = 'message'
    permission_required = 'mailing.change_message'

    def get_success_url(self):
        return reverse_lazy('mailing:message_detail', kwargs={'pk': self.object.pk})

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        # Если пользователь является владельцем объекта, допускаем доступ
        if user == obj.owner:
            return obj
        # Если пользователь не владелец, проверяем наличие права на изменение любых подписчиков
        elif user.has_perm('mailing.change_message'):
            return obj
        # Если пользователь не владелец и не имеет права на изменение, запрещаем доступ
        else:
            raise PermissionDenied("У Вас недостаточно прав для изменения.")


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    '''Удаление сообщения'''
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    context_object_name = 'message'
    success_url = reverse_lazy('mailing:message_list')
    permission_required = 'mailing.delete_message'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        # Если пользователь является владельцем объекта, допускаем доступ
        if user == obj.owner:
            return obj
        # Если пользователь не владелец, проверяем наличие права на изменение любых подписчиков
        elif user.has_perm('mailing.delete_message'):
            return obj
        # Если пользователь не владелец и не имеет права на изменение, запрещаем доступ
        else:
            raise PermissionDenied("У Вас недостаточно прав для удаления.")


class MailingModelListView(LoginRequiredMixin, ListView):
    '''Список рассылок'''
    model = MailingModel
    template_name = 'mailing/mailingmodel_list.html'
    context_object_name = 'mailingmodel_list'

    def get_queryset(self):
        user = self.request.user
        # Используем сервисную функцию и получаем список рассылок из кеша.
        # Если кеш пуст, то сервисная функция получает данные из БД
        return get_mailing_list_from_cache(user)

    # # без кеширования
    # def get_queryset(self):
    #     user = self.request.user
    #     try:
    #         # Получаем группу Owners
    #         owners_group = Group.objects.get(name='Owners')
    #         # Проверяем, состоит ли пользователь в группе Owners
    #         if owners_group in user.groups.all():
    #             # Если пользователь в группе Owners, возвращаем только его рассылки
    #             return MailingModel.objects.filter(owner=user)
    #         # Если пользователь не в группе Owners, проверяем наличие права на просмотр всех рассылок
    #         elif user.has_perm('mailing.view_mailingmodel'):
    #             # Если у пользователя есть разрешение, возвращаем все рассылки
    #             return MailingModel.objects.all()
    #     except Group.DoesNotExist:
    #         # Если группа Owners не найдена, возвращаем пустой список
    #         return MailingModel.objects.none()
    #     # Если пользователь не попадает ни в одну категорию, возвращаем пустой список
    #     return MailingModel.objects.none()


@method_decorator(cache_page(20), name='dispatch')
class MailingModelDetailView(LoginRequiredMixin, DetailView):
    '''Детальная информация о рассылке'''
    model = MailingModel
    template_name = 'mailing/mailingmodel_detail.html'
    context_object_name = 'mailingmodel'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        # Если пользователь является владельцем объекта, видит свой объект
        if user == obj.owner:
            return obj
        # Если пользователь не владелец, проверяем наличие права на просмотр всех подписчиков
        elif user.has_perm('mailing.view_mailingmodel'):
            return obj
        # Если пользователь не владелец и не имеет права на просмотр, запрещаем доступ
        else:
            raise PermissionDenied("У Вас недостаточно прав для просмотра.")


class MailingModelCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    '''Создание новой рассылки'''
    model = MailingModel
    form_class = MailingModelForm
    template_name = 'mailing/mailingmodel_form.html'
    success_url = reverse_lazy('mailing:mailingmodel_list')
    permission_required = 'mailing.add_mailingmodel'

    def get_form(self, form_class=None):
        """Переопределяем метод для ограничения доступности подписок и сообщений"""
        if not form_class:
            form_class = self.form_class
        form = form_class(**self.get_form_kwargs())  # Создаем экземпляр формы
        # Ограничиваем выбор сообщений и подписчиков текущим пользователем и
        # настраиваем queryset полей формы
        user = self.request.user
        form.fields['message'].queryset = Message.objects.filter(owner=user)
        form.fields['subscriber'].queryset = Subscriber.objects.filter(owner=user)
        return form

    def form_valid(self, form):
        mailing = form.save()
        user = self.request.user
        mailing.owner = user
        mailing.save()
        return super().form_valid(form)


class MailingModelUpdateView(LoginRequiredMixin, UpdateView):
    '''Изменение рассылки'''
    model = MailingModel
    form_class = MailingModelForm
    template_name = 'mailing/mailingmodel_form.html'
    context_object_name = 'mailingmodel'

    def get_success_url(self):
        return reverse_lazy('mailing:mailingmodel_detail', kwargs={'pk': self.object.pk})

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        # Если пользователь является владельцем объекта, допускаем доступ
        if user == obj.owner:
            return obj
        # Если пользователь не владелец, проверяем наличие права на изменение любых рассылок
        elif user.has_perm('mailing.change_mailingmodel'):
            return obj
        # Если пользователь не владелец и не имеет права на изменение, запрещаем доступ
        else:
            raise PermissionDenied("У Вас недостаточно прав для изменения.")


class MailingModelDeleteView(LoginRequiredMixin, DeleteView):
    '''Удаление рассылки'''
    model = MailingModel
    template_name = 'mailing/mailingmodel_confirm_delete.html'
    context_object_name = 'mailingmodel'
    success_url = reverse_lazy('mailing:mailingmodel_list')
    permission_required = 'mailing.delete_mailingmodel'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        # Если пользователь является владельцем объекта, допускаем доступ
        if user == obj.owner:
            return obj
        # Если пользователь не владелец, проверяем наличие права на изменение любых подписчиков
        elif user.has_perm('mailing.delete_mailingmodel'):
            return obj
        # Если пользователь не владелец и не имеет права на изменение, запрещаем доступ
        else:
            raise PermissionDenied("У Вас недостаточно прав для удаления.")


class DisableMailingView(LoginRequiredMixin, View):
    '''Деактивация рассылки'''
    def get(self, request, pk):
        # Получаем объект рассылки
        mailing = get_object_or_404(MailingModel, pk=pk)
        # Формируем и отправляем страницу подтверждения
        return render(request, 'mailing/confirm_disable_mailing.html', {'mailing': mailing})

    def post(self, request, pk):
        # Получаем объект модели
        mailing = get_object_or_404(MailingModel, pk=pk)
        # Получаем текущего пользователя
        user = self.request.user
        # Проверяем, обладает ли пользователь правом отключения рассылки
        if user.has_perm('mailing.can_disable_mailing'):
            # Если пользователь обладает правом отключения рассылки, деактивируем рассылку
            mailing.is_active = False
            mailing.save()
            # Подтверждение успешной операции
            messages.success(request, "Рассылка успешно отключена!")
        else:
            # Иначе сообщаем об ошибке
            messages.warning(request, "У вас нет прав отключить рассылку.")
        return redirect('mailing:mailingmodel_list')


class SendingMailingView(LoginRequiredMixin, View):
    '''Класс осуществляющий отправку рассылки и формирующий попытку рассылки (запись в БД о каждой
    попытке отправки сообщения по рассылке по каждому подписчику)'''

    def get(self, request, pk):
        mailing = get_object_or_404(MailingModel, pk=pk)
        user = self.request.user
        # Проверка владелец ли это данной рассылки
        if not user.has_perm('mailing.can_send_message'):
            messages.warning(request, 'У вас нет прав на управление этой рассылкой.')
            return redirect('mailing:mailingmodel_list')
        date_and_time_now = timezone.now()
        if date_and_time_now > mailing.end_sending:
            messages.warning(request, 'Время отправки рассылки закончилось! '
                                      'Статус рассылки будет изменен!')
            mailing.status = MailingModel.FINISHED
            mailing.save()
        if not mailing.is_active:
            messages.warning(request, 'Данная рассылка деактивирована модератором! '
                                      'Статус рассылки будет изменен!')
            mailing.status = MailingModel.FINISHED
            mailing.save()
        if mailing.status == MailingModel.FINISHED:
            messages.warning(request, 'Нельзя отправить завершённую рассылку!')
            return redirect('mailing:mailingmodel_list')
        return render(request, 'mailing/confirm_send.html', {'mailing': mailing})

    def post(self, request, pk):
        mailing = get_object_or_404(MailingModel, pk=pk)
        subject = mailing.message.subject
        body = mailing.message.body
        subscriber = mailing.subscriber.all()

        emails = [p.email for p in subscriber]

        if emails:
            for email in emails:
                try:
                    send_mail(
                        subject=subject,
                        message=body,
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                    messages.success(request, f'Рассылка отправлена получателю {email}.')
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
        else:
            messages.warning(request, 'У рассылки нет получателей.')

        return redirect('mailing:mailingmodel_list')


class MailingAttemptAllListView(LoginRequiredMixin, ListView):
    model = MailingAttempt
    template_name = 'mailing/mailing_attempt_all_list.html'
    context_object_name = 'attempt_list'


class MailingAttemptListView(LoginRequiredMixin, ListView):
    model = MailingAttempt
    template_name = 'mailing/mailingattempt_list.html'
    context_object_name = 'attempts'

    def get_queryset(self):
        return MailingAttempt.objects.filter(mailing_id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mailing'] = MailingModel.objects.get(pk=self.kwargs['pk'])
        return context
