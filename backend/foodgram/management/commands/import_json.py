import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from foodgram.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из файла JSON'

    def handle(self, *args, **kwargs):
        json_file_path = os.path.join(
            settings.BASE_DIR,
            'ingredients.json'
        )
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR(f'Файл {json_file_path} не найден.')
            )
            return
        except json.JSONDecodeError:
            self.stderr.write(
                self.style.ERROR('Ошибка в процессе декодирования JSON.')
            )
            return

        ingredients_to_create = []
        for item in data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')
            if name and measurement_unit:
                ingredients_to_create.append(
                    Ingredient(
                        name=str(name).strip(),
                        measurement_unit=measurement_unit
                    )
                )
        if not ingredients_to_create:
            self.stdout.write(
                self.style.WARNING(
                    'Нет валидных ингредиентов '
                    'для добавления после обработки JSON.'))
            return
        try:
            created_ingredients = Ingredient.objects.bulk_create(
                ingredients_to_create, 
                ignore_conflicts=True
            )
            self.stdout.write(
                self.style.SUCCESS('Загрузка ингредиентов успешно завершена.')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR('Произошла непредвиденная ошибка при '
                                 f'сохранении ингредиентов:: {e}'))
