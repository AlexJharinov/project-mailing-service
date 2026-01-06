from config.settings import CACHE_ENABLED
from django.core.cache import cache
from django.contrib.auth.models import Group
from mailing.models import Subscriber, Message, MailingModel


def get_subscriber_list_from_cache(user):
    '''Получает список получателей рассылки из кеша. Если кеш пуст, то получает данные из БД'''

    def get_subscriber_list():
        try:
            # Получаем группу Owners
            owners_group = Group.objects.get(name='Owners')
            # Проверяем, состоит ли пользователь в группе Owners
            if owners_group in user.groups.all():
                # Если пользователь в группе Owners, возвращаем только его подписчиков
                return Subscriber.objects.filter(owner=user)
            # Если пользователь не в группе Owners, проверяем наличие права на просмотр всех подписчиков
            elif user.has_perm('mailing.view_subscriber'):
                # Если у пользователя есть разрешение, возвращаем всех подписчиков
                return Subscriber.objects.all()
        except Group.DoesNotExist:
            # Если группа Owners не найдена, возвращаем пустой список
            return Subscriber.objects.none()
        # Если пользователь не попадает ни в одну категорию, возвращаем пустой список
        return Subscriber.objects.none()

    if not CACHE_ENABLED:
        return get_subscriber_list()

    # Получаем данные из кеша. Если кеш пуст, то получает данные из БД
    cache_key = f'subscriber_list_{user}'
    subscriber_list = cache.get(cache_key)
    if subscriber_list is not None:
        return subscriber_list
    subscriber_list = get_subscriber_list()
    cache.set(cache_key, subscriber_list, 20)
    return subscriber_list


def get_message_list_from_cache(user):
    '''Получает список сообщений из кеша. Если кеш пуст, то получает данные из БД'''

    def get_message_list():
        try:
            # Получаем группу Owners
            owners_group = Group.objects.get(name='Owners')
            # Проверяем, состоит ли пользователь в группе Owners
            if owners_group in user.groups.all():
                # Если пользователь в группе Owners, возвращаем только его сообщения
                return Message.objects.filter(owner=user)
            # Если пользователь не в группе Owners, проверяем наличие права на просмотр всех сообщений
            elif user.has_perm('mailing.view_message'):
                # Если у пользователя есть разрешение, возвращаем все сообщения
                return Message.objects.all()
        except Group.DoesNotExist:
            # Если группа Owners не найдена, возвращаем пустой список
            return Message.objects.none()
        # Если пользователь не попадает ни в одну категорию, возвращаем пустой список
        return Message.objects.none()

    if not CACHE_ENABLED:
        return get_message_list()

    # Получаем данные из кеша. Если кеш пуст, то получает данные из БД
    cache_key = f'message_list_{user}'
    message_list = cache.get(cache_key)
    if message_list is not None:
        return message_list
    message_list = get_message_list()
    cache.set(cache_key, message_list, 20)
    return message_list


def get_mailing_list_from_cache(user):
    '''Получает список рассылок из кеша. Если кеш пуст, то получает данные из БД'''

    def get_mailing_list():
        try:
            # Получаем группу Owners
            owners_group = Group.objects.get(name='Owners')
            # Проверяем, состоит ли пользователь в группе Owners
            if owners_group in user.groups.all():
                # Если пользователь в группе Owners, возвращаем только его рассылки
                return MailingModel.objects.filter(owner=user)
            # Если пользователь не в группе Owners, проверяем наличие права на просмотр всех рассылок
            elif user.has_perm('mailing.view_mailingmodel'):
                # Если у пользователя есть разрешение, возвращаем все рассылки
                return MailingModel.objects.all()
        except Group.DoesNotExist:
            # Если группа Owners не найдена, возвращаем пустой список
            return MailingModel.objects.none()
        # Если пользователь не попадает ни в одну категорию, возвращаем пустой список
        return MailingModel.objects.none()

    if not CACHE_ENABLED:
        return get_mailing_list()

    # Получаем данные из кеша. Если кеш пуст, то получает данные из БД
    cache_key = f'message_list_{user}'
    mailing_list = cache.get(cache_key)
    if mailing_list is not None:
        return mailing_list
    mailing_list = get_mailing_list()
    cache.set(cache_key, mailing_list, 20)
    return mailing_list