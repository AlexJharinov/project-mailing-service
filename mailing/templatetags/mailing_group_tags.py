from django import template
# from django.contrib.auth.models import Group

register = template.Library()


@register.filter(name='in_group')
def in_group(user, group_name):
    """Возвращает True, если пользователь входит в указанную группу."""
    return user.groups.filter(name=group_name).exists()
