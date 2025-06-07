from rest_framework import status
from rest_framework.response import Response

from .serializers import FollowSerializer, RecipeMiniSerializer


def check_and_create(model, item, user, serializer_context=None, item_type='recipe'):
    """Добавляет или создает объект (рецепт или подписку)."""
    if not model.objects.filter(user=user, **{item_type: item}).exists():
        model.objects.create(user=user, **{item_type: item})
        if item_type == 'recipe':
            serializer = RecipeMiniSerializer(item)
        elif item_type == 'following':
            serializer = FollowSerializer(item, context=serializer_context)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(
        {'error': f'Объект {item_type} уже добавлен.'},
        status=status.HTTP_400_BAD_REQUEST
    )


def check_and_delete(model, item, user, item_type='recipe'):
    """Удаляет объект (рецепт или подписку)."""
    try:
        object = model.objects.get(user=user, **{item_type: item})
        object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except model.DoesNotExist:
        return Response(
            {'error': f'Объект {item_type} не найден.'},
            status=status.HTTP_400_BAD_REQUEST
        )
