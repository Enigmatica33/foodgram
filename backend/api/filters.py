from django_filters import rest_framework as filters

from foodgram.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    """Фильтр для поиска ингредиента по названию."""
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(filters.FilterSet):
    """Фильтр для поиска рецепта по автору."""
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='is_favorited_method')
    is_in_shopping_cart = filters.BooleanFilter(
        method='is_in_shopping_cart_method'
    )

    # def is_favorited_method(self, queryset, name, value):
    #     if value and self.request.user.is_authenticated:
    #         return queryset.filter(recipe_favorite__user=self.request.user)
    #     return queryset

    # def is_in_shopping_cart_method(self, queryset, name, value):
    #     if value and self.request.user.is_authenticated:
    #         return queryset.filter(
    # recipe_shoppingcart__user=self.request.user)
    #     return queryset

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart', 'tags']
