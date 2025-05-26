from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constants import (MAX_EMAIL, MAX_INGREDIENTS, MAX_MEASUREMENT_UNIT,
                        MAX_RECIPE_NAME, MAX_TAG, MAX_USER)
from .validators import validate_name


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, max_length=MAX_EMAIL)
    username = models.CharField(
        max_length=MAX_USER,
        # blank=False,
        # null=False,
        unique=True,
        validators=[RegexValidator(regex=r'^[\w.@+-]+\Z'), validate_name]
    )
    first_name = models.CharField(
        max_length=MAX_USER,
        blank=True,
        validators=[validate_name]
    )
    last_name = models.CharField(
        max_length=MAX_USER,
        blank=True,
        validators=[validate_name]
    )
    password = models.CharField(max_length=MAX_USER)
    avatar = models.ImageField(
        upload_to='foodgram/images/',
        null=True,
        default=None
    )
    is_subscribed = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_TAG,
        unique=True,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        max_length=MAX_TAG,
        unique=True,
        verbose_name='Slug'
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_INGREDIENTS,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT,
        verbose_name='Единицы измерения'
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    # related_name='recipes' – этот параметр задает обратное имя для связи.
    # Это означает, что вы сможете получить все рецепты,
    # связанные с конкретным автором, используя
    #           author_instance.recipes.all(),
    # где author_instance – это экземпляр модели CustomUser.
    # Это удобно для запроса всех рецептов,
    # связанных с определенным пользователем.
    name = models.CharField(
        max_length=MAX_RECIPE_NAME,
        verbose_name='Название рецепта'
    )
    text = models.TextField(verbose_name='Описание рецепта')
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    image = models.ImageField(
        upload_to='foodgram/',
        null=True,
        blank=True,
        verbose_name='Изображение'
    )
    cooking_time = models.SmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления (мин.)',
        help_text='время приготовления не должно быть меньше 1 минуты'
    )

    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления рецепта'
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('pub_date',)

    def __str__(self):
        return f'{self.name} от {self.author}'


class RecipeTag(models.Model):
    """Связь Рецептов и Тегов"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='Рецепт',
    )

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег',
    )

    def __str__(self):
        return f'{self.recipe} {self.tag}'


class RecipeIngredient(models.Model):
    """Связь Рецептов и Ингредиентов"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='Рецепт',
        related_name='recipeingredient'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipeingredient'
    )
    amount = models.IntegerField(null=True)

    class Meta:
        pass
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=('recipe', 'ingredient'),
        #         name='unique_recipe_ingredient'
        #     )
        # ]

    def __str__(self):
        return f'{self.recipe} {self.ingredient}'


class Follow(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор рецепта'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('following',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_following_check'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='self_following_check'
            ),
        ]

    def __str__(self):
        return self.following


class ShoppingCart(models.Model):
    """Корзина покупок."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='user_shopping',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        related_name='recipe_shopping',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'корзины'
        ordering = ('recipe',)

    def __str__(self):
        return f'{self.user} {self.recipe}'


class Favorite(models.Model):
    """Избранное."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='user_favorite',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        related_name='recipe_favorite',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ('recipe',)

    def __str__(self):
        return f'{self.user} {self.recipe}'
