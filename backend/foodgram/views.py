from django.shortcuts import redirect
from rest_framework import status
from rest_framework.response import Response

from .models import Recipe


def redirect_from_short_link(request, recipe_hash):
    """Редирект короткой ссылки на страницу рецепта."""
    try:
        recipe = Recipe.objects.get(short_link=recipe_hash)
        return redirect(recipe)
    except Recipe.DoesNotExist:
        return Response(
            {'error': f'Рецепт {recipe} не найден.'},
            status=status.HTTP_404_NOT_FOUND
        )
