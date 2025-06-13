import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from .constants import (MAX_AMOUNT, MAX_EMAIL, MAX_INGREDIENTS,
                        MAX_MEASUREMENT_UNIT, MAX_RECIPE_NAME, MAX_TAG_NAME,
                        MAX_TAG_SLUG, MAX_TIME, MAX_USER, MIN_AMOUNT, MIN_TIME)


class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=MAX_EMAIL)
    username = models.CharField(
        max_length=MAX_USER,
        unique=True,
        validators=[RegexValidator(regex=r'^[\w.@+-]+\Z')]
    )
    first_name = models.CharField(
        max_length=MAX_USER,
    )
    last_name = models.CharField(
        max_length=MAX_USER,
    )
    avatar = models.ImageField(
        upload_to='foodgram/images/',
        null=True,
        default=None
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_TAG_NAME,
        unique=True,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        max_length=MAX_TAG_SLUG,
        unique=True,
        verbose_name='Slug'
    )

    class Meta:
        ordering = ('name',)
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
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit'
            )
        ]

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME,
        verbose_name='Название рецепта'
    )
    text = models.TextField(verbose_name='Описание рецепта')
    tags = models.ManyToManyField(
        Tag,
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
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_TIME), MaxValueValidator(MAX_TIME)],
        verbose_name='Время приготовления (мин.)',
        help_text='время приготовления не должно быть '
        f'меньше {MIN_TIME} минуты'
    )
    short_link = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Короткая ссылка на рецепт'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления рецепта'
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'Рецепт {self.name} от пользователя {self.author}'

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def generate_short_link(self):
        recipe_hash = uuid.uuid4().hex[:3]
        return recipe_hash

    def get_absolute_url(self):
        return f'/recipes/{self.pk}/'


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
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ]
    )

    class Meta:
        ordering = ('recipe',)
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.recipe} {self.ingredient}'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        User,
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


class UserRecipeBase(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='user_%(class)s'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='Рецепт',
        related_name='recipe_%(class)s'
    )

    class Meta:
        abstract = True
        ordering = ('recipe',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(app_label)s_%(class)s_user_recipe_unique'
            )
        ]


class ShoppingCart(UserRecipeBase):
    """Корзина покупок."""

    class Meta(UserRecipeBase.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'корзины'

    def __str__(self):
        return (
            f'Пользователь {self.user} добавил '
            f'в корзину рецепт {self.recipe}'
        )


class Favorite(UserRecipeBase):
    """Избранное."""

    class Meta(UserRecipeBase.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return (
            f'Пользователь {self.user} добавил '
            f'в избранное рецепт {self.recipe}'
        )
