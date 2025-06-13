from django.shortcuts import redirect
from rest_framework.exceptions import NotFound

from .models import Recipe


def redirect_from_short_link(request, recipe_hash):
    """Редирект короткой ссылки на страницу рецепта."""
    try:
        recipe = Recipe.objects.get(short_link=recipe_hash)
        return redirect(recipe)
    except Recipe.DoesNotExist:
        raise NotFound('Рецепт не найден!')
