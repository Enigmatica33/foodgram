from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .serializers import RecipeMiniSerializer


def create_favorite_cart(model, recipe, user):
    """Добавляет рецепт в избранное/корзину."""
    instance, created = model.objects.get_or_create(
        user=user,
        recipe=recipe
    )
    if created:
        serializer = RecipeMiniSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(
        {'error': 'Рецепт уже добавлен в избранное'},
        status=status.HTTP_400_BAD_REQUEST
    )


def delete_from_favorite_cart(model, recipe, user):
    """Удаляет рецепт из избранного/корзины."""
    deleted_count, _ = model.objects.filter(user=user, recipe=recipe).delete()
    if deleted_count > 0:
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(
        {'error': f'Рецепт {recipe} не найден.'},
        status=status.HTTP_400_BAD_REQUEST
    )


def get_recipes_limit(request):
    """Получает параметр recipes_limit из запроса."""
    recipes_limit_str = request.query_params.get('recipes_limit')
    if recipes_limit_str:
        try:
            return int(recipes_limit_str)
        except ValueError:
            raise ValidationError(
                {'recipes_limit':
                 'Параметр recipes_limit должен быть целым числом.'}
            )
    return None
