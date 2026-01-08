from django.core.cache import cache

from config.settings import CACHE_ENABLED
from mailing.models import Subscriber, Message, MailingModel

CACHE_TTL = 20  # секунд


def _key(prefix: str, user) -> str:
    return f"{prefix}_list_user_{user.pk}"


def get_subscriber_list_from_cache(user):
    """Получает список получателей из кеша. Если кеш выключен/пуст — из БД."""
    if user.is_superuser or user.has_perm("mailing.view_subscriber"):
        qs = Subscriber.objects.all()
    else:
        qs = Subscriber.objects.filter(owner=user)

    if not CACHE_ENABLED:
        return qs

    cache_key = _key("subscriber", user)
    data = cache.get(cache_key)
    if data is not None:
        return data

    data = list(qs)
    cache.set(cache_key, data, CACHE_TTL)
    return data


def get_message_list_from_cache(user):
    """Получает список сообщений из кеша. Если кеш выключен/пуст — из БД."""
    if user.is_superuser or user.has_perm("mailing.view_message"):
        qs = Message.objects.all()
    else:
        qs = Message.objects.filter(owner=user)

    if not CACHE_ENABLED:
        return qs

    cache_key = _key("message", user)
    data = cache.get(cache_key)
    if data is not None:
        return data

    data = list(qs)
    cache.set(cache_key, data, CACHE_TTL)
    return data


def get_mailing_list_from_cache(user):
    """Получает список рассылок из кеша. Если кеш выключен/пуст — из БД."""
    if user.is_superuser or user.has_perm("mailing.view_mailingmodel"):
        qs = MailingModel.objects.all()
    else:
        qs = MailingModel.objects.filter(owner=user)

    if not CACHE_ENABLED:
        return qs

    cache_key = _key("mailing", user)  #
    data = cache.get(cache_key)
    if data is not None:
        return data

    data = list(qs)
    cache.set(cache_key, data, CACHE_TTL)
    return data
