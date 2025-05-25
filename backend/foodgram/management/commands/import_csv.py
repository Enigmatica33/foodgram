import csv

from django.core.management.base import BaseCommand
from foodgram.models import (
    Ingredient
)

model_csv_dict = {
    'data/ingredients.csv': Ingredient
}


class Command(BaseCommand):
    """Команда для импорта Ингредиентов из CSV файла."""

    help = 'Импорт Ингредиентов'

    def create_row_fields(self, row):
        """Дополняет строку таблицы экземплярами модели."""
        try:
            if row.get('name'):
                row['name'] = Ingredient.objects.get(pk=row['author'])
            if row.get('review_id'):
                row['review'] = Review.objects.get(pk=row['review_id'])
            if row.get('title_id'):
                row['title'] = Title.objects.get(pk=row['title_id'])
            if row.get('category'):
                row['category'] = Category.objects.get(pk=row['category'])
            if row.get('genre'):
                row['genre'] = Genre.objects.get(pk=row['genre'])
        except Exception as error:
            print(f'Ошибка в строке {row.get("id")}.'
                  f'Текст - {error}')
        return row

    def handle(self, *args, **options):
        for i in model_csv_dict.items():
            path, model = i
            rows = 0
            successful = 0
            print(f'Заполняем модель {model.__name__}')
            with open(path, encoding='utf-8', mode='r') as file:
                csv_read = csv.DictReader(file)
                for row in csv_read:
                    rows += 1
                    row = self.create_row_fields(row)
                    try:
                        model.objects.get_or_create(**row)
                        successful += 1
                    except Exception as error:
                        print(f'Ошибка в строке {row.get("id")}.'
                              f'Текст - {error}')
            print(f'Заполнение модели {model.__name__} завершено. '
                  f'Строк: {rows}. Успешно добавлено: {successful}.',
                  )
