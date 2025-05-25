from django_filters import rest_framework as filters

from foodgram.models import CustomUser, Ingredient, Recipe, Tag


class NameSearchFilter(filters.FilterSet):
    """Фильтр для ингредиента по названию."""
    name = filters.CharFilter(field_name='name', method='filter_by_name')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(name__istartswith=value)


class AuthorSearchFilter(filters.FilterSet):
    """Фильтр для поиска рецепта по автору."""
    author = filters.NumberFilter(
        field_name='author',
    )

    class Meta:
        model = Recipe
        fields = ['author']


class TagFilter(filters.FilterSet):
    tags = filters.CharFilter(field_name='tags__slug', method='filter_by_name')

    class Meta:
        model = Recipe
        fields = ['tags__slug']

    def filter_by_name(self, queryset, tags__slug, value):
        return queryset.filter(tags__slug=value)



    # """Фильтр для поиска рецепта по тегам."""
    # tag = filters.ModelMultipleChoiceFilter(
    #     queryset=Tag.objects.all(),
    #     field_name='tags__slug',
    #     to_field_name='slug'
    # )

    # class Meta:
    #     model = Recipe
    #     fields = ['tags']

    # @classmethod
    # def get_choices(cls):
    #     # Извлечение уникальных значений категорий из базы данных
    #     return Tag.objects.values_list('slug', flat=True).distinct()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # Установка динамических choices
    #     self.base_filters['tags'].extra['choices'] = self.get_choices()
