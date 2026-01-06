from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Загружает исходные групповые данные из groups.json'

    def handle(self, *args, **options):
        try:
            call_command('loaddata', 'groups.json')
            self.stdout.write(self.style.SUCCESS('Успешно загружен groups.json'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ошибка при загрузке данных: {e}'))