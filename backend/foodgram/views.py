from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def redirect_from_short_link(request, recipe_hash):
    """Редирект короткой ссылки на страницу рецепта."""
    recipe = get_object_or_404(Recipe, short_link=recipe_hash)
    return redirect(recipe)
