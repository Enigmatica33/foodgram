from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from foodgram.models import (Follow, Ingredient, Recipe, RecipeIngredient, Tag,
                             User)

from .fields import Base64ImageField


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для Пользователей."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        """Определяем значение поля is_subscribed для отображения."""
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and Follow.objects.filter(
                    user=request.user,
                    following=obj).exists())


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара."""
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        if not data.get('avatar'):
            raise serializers.ValidationError(
                'Поле аватар не должно быть пустым'
            )
        return data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для Тегов в рецепте."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка Ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeIngredient."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount', 'name', 'measurement_unit')


class RecipeMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для записи рецептов."""
    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        if not data.get('tags'):
            raise serializers.ValidationError('Укажите хотя бы один тэг.')
        if not data.get('ingredients'):
            raise serializers.ValidationError('Укажите ингредиенты.')
        ingredient_ids = set()
        for ingredients in data['ingredients']:
            ingredient_id = ingredients['id']
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    f'Ингредиент c ID {ingredient_id} уже указан.'
                )
            ingredient_ids.add(ingredient_id)
        if len(data.get('tags')) != len(set(data.get('tags'))):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return data

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Добавьте изображение.')
        return value

    def create_recipe_ingredient(self, ingredients, recipe):
        """Создание записи в таблице RecipeIngredient."""
        recipe_ingredients_to_create = []
        for data in ingredients:
            ingredient = data['id']
            amount = data['amount']
            recipe_ingredients_to_create.append(
                RecipeIngredient(
                    ingredient=ingredient,
                    recipe=recipe,
                    amount=amount
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients_to_create)

    def create_recipe_tag(self, tags, recipe):
        """Создание записи в таблице RecipeTag."""
        recipe.tags.set(tags)

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        self.create_recipe_ingredient(ingredients, recipe)
        self.create_recipe_tag(tags, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.ingredients.clear()
        instance.tags.clear()
        self.create_recipe_ingredient(ingredients, instance)
        self.create_recipe_tag(tags, instance)
        return instance

    def to_representation(self, instance):
        """Метод для представления созданного рецепта."""
        serializer = RecipeReadSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        )
        return serializer.data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов на чтение."""
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient',
        many=True
    )
    author = UserSerializer()
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        )


class FollowSerializer(UserSerializer):
    """Сериализатор для Подписок."""
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )
        read_only_fields = ('email', 'username')

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        request = self.context.get('request')
        recipes_limit_str = request.query_params.get('recipes_limit')
        if recipes_limit_str:
            try:
                recipes_limit = int(recipes_limit_str)
                recipes = recipes[:recipes_limit]
            except ValueError:
                raise ValidationError(
                    {'recipes_limit':
                        'Параметр recipes_limit должен быть целым числом.'}
                )
        return RecipeMiniSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    @staticmethod
    def get_recipes_count(obj):
        """Метод для получения количества рецептов."""
        return obj.recipes.count()

    def validate_following(self, value):
        if self.context['request'].user == value:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )
        return value
