from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .serializers import FollowSerializer, RecipeMiniSerializer


def check_and_create(model, item, user, serializer_context=None,
                     item_type='recipe'):
    """Добавляет или создает объект (рецепт или подписку)."""
    if not model.objects.filter(user=user, **{item_type: item}).exists():
        model.objects.create(user=user, **{item_type: item})
        if item_type == 'recipe':
            serializer = RecipeMiniSerializer(item)
        elif item_type == 'following':
            serializer = FollowSerializer(item, context=serializer_context)
        if serializer:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error':
                 f'Неизвестный item_type: {item_type} для сериализации.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    return Response(
        {'error': f'Объект {item_type} уже добавлен.'},
        status=status.HTTP_400_BAD_REQUEST
    )


def check_and_delete(model, item, user, item_type='recipe'):
    """Удаляет объект (рецепт или подписку)."""
    try:
        obj_to_delete = model.objects.get(user=user, **{item_type: item})
        obj_to_delete.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except model.DoesNotExist:
        return Response(
            {'error': f'Объект {item_type} не найден.'},
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
