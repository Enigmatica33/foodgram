import json

from django.core.management.base import BaseCommand

from foodgram.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из файла JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Файл для импорта'
        )

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                for item in data:
                    ingredient, created = Ingredient.objects.get_or_create(
                        name=item['name'],
                        defaults={
                            'measurement_unit': item['measurement_unit']
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f'Ингредиент {ingredient.name} добавлен.'
                        ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'Ингредиент {ingredient.name} уже существует.'
                        ))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR('Файл не найден.'))
        except json.JSONDecodeError:
            self.stderr.write(
                self.style.ERROR('Ошибка в процессе декодирования JSON.')
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ошибка: {e}'))
