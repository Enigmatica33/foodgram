import hashlib

from django.db.models import BooleanField, Exists, Prefetch, OuterRef, Sum, Value
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from foodgram.models import (Favorite, Follow, Ingredient, Recipe,
                             RecipeIngredient, ShoppingCart, Tag, User)

from .filters import IngredientFilter, RecipeFilter
from .functions import create_favorite_cart, delete_from_favorite_cart
from .pagination import Pagination
from .pdf import pdf_creating
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, FollowSerializer,
                          IngredientListSerializer, RecipeReadSerializer,
                          RecipeSerializer, TagSerializer, UserSerializer)


class UserViewSet(UserViewSet):
    """Представление для Пользователя."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = Pagination
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = (AllowAny,)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """Создание подписки."""
        author = get_object_or_404(User, id=id)
        user = request.user
        serializer_context = {
            'request': request
        }
        if user == author:
            return Response(
                {'error': 'Нельзя подписываться на самого себя!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance, created = Follow.objects.get_or_create(
                user=user,
                following=author
            )
        if created:
            serializer = FollowSerializer(author, context=serializer_context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'detail': 'Подписка уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Удаление подписки."""
        try:
            author = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(
                {'error': f'Автор с ID {id} не найден. '
                 'Невозможно отписаться.'},
                status=status.HTTP_404_NOT_FOUND
            )
        user = request.user
        deleted_count, _ = Follow.objects.filter(
            user=user,
            following=author
        ).delete()
        if deleted_count > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'error': f'Подписка на автора {author} не найдена.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Просмотр подписок."""
        subscriptions = User.objects.filter(
            following__user=request.user
        ).prefetch_related('recipes').order_by('username')
        paginator = Pagination()
        serializer_context = {
            'request': request,
        }
        result_pages = paginator.paginate_queryset(
            subscriptions,
            request
        )
        serializer = FollowSerializer(
            result_pages,
            many=True,
            context=serializer_context
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=False,
        url_name='me',
        url_path='me',
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        """Управление персональными данными пользователя."""
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['put', 'delete'],
        url_name='me/avatar',
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def update_avatar(self, request):
        """Добавление/удаление аватара."""
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для Рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    permission_classes = (
        AllowAny,
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly
    )
    pagination_class = Pagination
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags',
            'recipeingredient__ingredient'
        )
        if user.is_authenticated:
            queryset = queryset.annotate(is_favorited=Exists(
                Favorite.objects.filter(
                    user=user,
                    recipe=OuterRef('pk')
                )),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe=OuterRef('pk')
                    )
            ))
        else:
            queryset = queryset.annotate(
                is_favorited=Value(False),
                is_in_shopping_cart=Value(False)
            )
        return queryset

    def get_serializer_class(self):
        """Определяем тип Сериализатора."""
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeSerializer

    @action(detail=True, url_path='get-link', url_name='get-link')
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            raise NotFound('Рецепт не найден!')
        recipe_hash = hashlib.md5(str(recipe.pk).encode()).hexdigest()[:3]
        short_link = request.build_absolute_uri(f'/s/{recipe_hash}/')
        recipe.short_link = recipe_hash
        recipe.save()
        return Response({'short-link': short_link})

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        url_name='favorite',
        permission_classes=(IsAuthenticated,)
    )
    def get_favorite(self, request, pk=None):
        """Добавление рецепта в избранное."""
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            return create_favorite_cart(Favorite, recipe, user)
        return delete_from_favorite_cart(Favorite, recipe, user)

    @action(
        detail=True,
        url_path='shopping_cart',
        url_name='shopping_cart',
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def get_shopping_cart(self, request, pk=None):
        """Добавление рецепта в корзину."""
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            return create_favorite_cart(
                ShoppingCart,
                recipe,
                user,
            )
        return delete_from_favorite_cart(
            ShoppingCart,
            recipe,
            user,
        )

    @action(
        detail=False,
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def get_download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__recipe_shoppingcart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount')).order_by('ingredient__name')
        return pdf_creating(self, ingredients, request.user.username)


class TagViewSet(viewsets.ModelViewSet):
    """Представление для Тэгов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    http_method_names = ['get']


class IngredientViewSet(viewsets.ModelViewSet):
    """Представление для Ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientListSerializer
    pagination_class = None
    filterset_class = IngredientFilter
    http_method_names = ['get']
