from django.shortcuts import redirect, render

from .models import Recipe


def redirect_from_short_link(request, recipe_hash):
    """Редирект короткой ссылки на страницу рецепта."""
    try:
        recipe = Recipe.objects.get(short_link=recipe_hash)
        return redirect(recipe)
    except Recipe.DoesNotExist:
        return redirect('/404')


def custom_page_not_found_view(request, exception):
    return render(request, 'recipes', status=404)
