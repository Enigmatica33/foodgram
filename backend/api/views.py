import hashlib

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from foodgram.models import (CustomUser, Favorite, Follow, Ingredient, Recipe,
                             RecipeIngredient, ShoppingCart, Tag)

from .filters import IngredientFilter, RecipeFilter
from .functions import check_and_create, check_and_delete
from .pagination import CustomPagination
from .pdf import pdf_creating
from .permissions import IsAuthor, IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, CustomUserCreateSerializer,
                          CustomUserSerializer, FollowSerializer,
                          IngredientListSerializer, MeSerializer,
                          RecipeReadSerializer, RecipeSerializer,
                          TagListSerializer)


class CustomUserViewSet(viewsets.ModelViewSet):
    """Представление для Пользователя."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = (AllowAny,)

    def create(self, request):
        serializer = CustomUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['get', 'post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        """Создание подписки."""
        author = get_object_or_404(CustomUser, id=pk)
        user = request.user
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'Нельзя подписываться на самого себя!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return check_and_create(
                Follow,
                author,
                user,
                item_type='following'
            )
        if request.method == 'DELETE':
            return check_and_delete(
                Follow,
                author,
                user,
                item_type='following'
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Просмотр и управление подписками."""
        subscriptions = CustomUser.objects.filter(
            following__user=request.user
        ).order_by('username')
        paginator = CustomPagination()
        page = request.query_params.get('page')
        limit = request.query_params.get('limit')
        recipes_limit = request.query_params.get('recipes_limit')
        try:
            page = int(page)
            limit = int(limit)
            recipes_limit = int(recipes_limit)
            if page <= 0 or limit <= 0 or recipes_limit <= 0:
                raise ValueError('Неверное значение параметров.')
        except ValueError:
            return Response(
                {"error": "Параметры 'page', 'limit', 'recipes_limit' "
                    "должны быть положительными целыми числами."},
                status=status.HTTP_400_BAD_REQUEST
            )
        result_pages = paginator.paginate_queryset(
            subscriptions,
            request
        )
        serializer = FollowSerializer(
            result_pages,
            many=True,
            context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request):
        """Управление персональными данными пользователя."""
        user = request.user
        serializer = MeSerializer(user)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['put', 'delete'],
        url_path='avatar',
        permission_classes=(IsAuthenticated,)
    )
    def update_avatar(self, request, pk=None):
        """Добавление/удаление аватара."""
        user = request.user
        if request.method == 'PUT':
            if 'avatar' not in request.data or not request.data['avatar']:
                return Response(
                    {'error': 'Добавьте аватар.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = AvatarSerializer(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        elif request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        url_path='set_password',
        url_name='set_password',
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request, pk=None):
        user = request.user
        if user is None:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        errors = []
        if not user.check_password(current_password):
            errors.append('Неверный текущий пароль!')
        if not new_password:
            errors.append('Новый пароль не указан!')
        if errors:
            return Response(
                {'errors': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для Рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination
    filterset_class = RecipeFilter

    def get_permissions(self):
        """Определяем права доступа для разных методов."""
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated]
        elif self.request.method == 'PATCH':
            self.permission_classes = [IsAuthorOrReadOnly]
        elif self.request.method == 'DELETE' and self.action == 'get_favorite':
            self.permission_classes = [IsAuthenticated]
        elif (self.request.method == 'DELETE'
              and self.action == 'get_shopping_cart'):
            self.permission_classes = [IsAuthenticated]
        elif self.request.method == 'DELETE':
            self.permission_classes = [IsAuthorOrReadOnly]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Авторизованный пользователь создает пост."""
        serializer.save(author=self.request.user)

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
        full_url = f'{request.scheme}://{request.get_host()}'
        recipe_hash = hashlib.md5(str(recipe.pk).encode()).hexdigest()[:3]
        short_link = f'{full_url}/s/{recipe_hash}'
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
            return check_and_create(Favorite, recipe, user, item_type='recipe')
        if request.method == 'DELETE':
            return check_and_delete(Favorite, recipe, user, item_type='recipe')

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
            return check_and_create(
                ShoppingCart,
                recipe,
                user,
                item_type='recipe'
            )
        if request.method == 'DELETE':
            return check_and_delete(
                ShoppingCart,
                recipe,
                user,
                item_type='recipe'
            )

    @action(
        detail=False,
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
        permission_classes=(IsAuthenticated, IsAuthor)
    )
    def get_download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__recipe_shopping__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount')).order_by('ingredient__name')
        return pdf_creating(self, ingredients, request.user.username)


class TagViewSet(viewsets.ModelViewSet):
    """Представление для Тэгов."""
    queryset = Tag.objects.all()
    serializer_class = TagListSerializer
    pagination_class = None
    http_method_names = ['get']


class IngredientViewSet(viewsets.ModelViewSet):
    """Представление для Ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientListSerializer
    pagination_class = None
    filterset_class = IngredientFilter
    http_method_names = ['get']
