import hashlib
from io import BytesIO

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from foodgram.models import (CustomUser, Favorite, Follow, Ingredient, Recipe,
                             RecipeIngredient, ShoppingCart, Tag)

from .filters import AuthorSearchFilter, NameSearchFilter
from .permissions import IsAuthor, IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, CustomUserCreateSerializer,
                          CustomUserSerializer, FollowSerializer,
                          IngredientListSerializer, MeSerializer,
                          RecipeMiniSerializer, RecipeReadSerializer,
                          RecipeSerializer, TagListSerializer)


class CustomUserViewSet(viewsets.ModelViewSet):
    """Представление для Пользователя."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitOffsetPagination
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
        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'error': 'Нельзя подписываться на самого себя!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not Follow.objects.filter(
                user=request.user,
                following=author
            ).exists():
                serializer = FollowSerializer(author)
                Follow.objects.create(user=request.user, following=author)
            else:
                return Response(
                    {'detail': 'Подписка уже существует'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            try:
                subscription = Follow.objects.get(
                    user=request.user,
                    following=author
                )
            except Follow.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get', 'post'])
    def subscriptions(self, request):
        """Просмотр и управление своими подписками."""
        user = request.user
        subscriptions = user.following.all()
        # page = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(subscriptions, many=True)
        return self(serializer.data)

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
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        errors = []
        if not user.check_password(current_password):
            errors.append('Неверный текущий пароль')
        if not new_password:
            errors.append('Новый пароль не предоставлен')
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
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = AuthorSearchFilter

    def get_permissions(self):
        """Определяем права доступа для создания и обновления."""
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated]
        elif self.request.method in ['PUT', 'PATCH', 'DELETE']:
            self.permission_classes = [IsAuthorOrReadOnly]
        else:
            self.permission_classes = [AllowAny]

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
            raise NotFound("Recipe not found")
        full_url = f'{request.scheme}://{request.get_host()}'
        recipe_hash = hashlib.md5(str(recipe.pk).encode()).hexdigest()[:3]
        short_link = f'{full_url}/s/{recipe_hash}'
        return Response({'short-link': short_link})

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(AllowAny,)
    )
    def get_favorite(self, request, pk=None):
        """Добавление рецепта в избранное."""
        recipe = self.get_object()
        if request.method == 'POST':
            if not Favorite.objects.filter(
                user=request.user,
                recipe__id=pk
            ).exists():
                serializer = RecipeMiniSerializer(recipe)
                Favorite.objects.create(user=request.user, recipe=recipe)
            else:
                return Response(
                    {'detail': 'Рецепт уже добавлен в избранное'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(
                    user=request.user,
                    recipe=recipe
                )
            except Favorite.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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
        if request.method == 'POST':
            if not ShoppingCart.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():
                serializer = RecipeMiniSerializer(recipe)
                ShoppingCart.objects.create(user=request.user, recipe=recipe)
            else:
                return Response(
                    {'detail': 'Рецепт уже добавлен в корзину'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            try:
                shopping_cart = ShoppingCart.objects.get(
                    user=request.user,
                    recipe=recipe
                )
            except ShoppingCart.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        p.setFont('DejaVuSans', 16)
        p.drawString(100, height - 50, 'Список покупок')
        y_position = height - 100
        p.setFont('DejaVuSans', 20)
        for ingredient in ingredients:
            text = f"-{ingredient['ingredient__name']}: {ingredient['amount']}"
            f"{ingredient['ingredient__measurement_unit']}"
            p.drawString(100, y_position, text.encode('utf-8').decode('utf-8'))
            y_position -= 30
            if y_position < 50:
                p.showPage()
                p.setFont('DejaVuSans', 12)
                y_position = height - 100
        p.save()
        buffer.seek(0)
        response = HttpResponse(
            buffer,
            content_type='application/pdf'
        )
        response['Content-Disposition'] = 'attachment; '
        f'filename="{request.user.username}_shopping_list.pdf"'
        return response


class TagViewSet(viewsets.ModelViewSet):
    """Представление для Тэгов."""
    queryset = Tag.objects.all()
    serializer_class = TagListSerializer
    pagination_class = None
    http_method_names = ['get',]


class IngredientViewSet(viewsets.ModelViewSet):
    """Представление для Ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientListSerializer
    pagination_class = None
    filterset_class = NameSearchFilter
    http_method_names = ['get']


class FollowViewSet(viewsets.ModelViewSet):
    """Представление для подписок."""
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.create(serializer.validated_data)
