from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import EmailValidator, MaxLengthValidator
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from foodgram.constants import (ERROR_MESSAGE_CHECK_LENGTH,
                                ERROR_MESSAGE_DOUBLE_EMAIL,
                                ERROR_MESSAGE_DOUBLE_USERNAME,
                                ERROR_MESSAGE_REGEX, MAX_USER)
from foodgram.models import (CustomUser, Favorite, Follow, Ingredient, Recipe,
                             RecipeIngredient, RecipeTag, ShoppingCart, Tag)

from .fields import Base64ImageField


class CustomUserCreateSerializer(UserCreateSerializer):
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(
        required=True,
        validators=[MaxLengthValidator(
            MAX_USER,
            message=ERROR_MESSAGE_CHECK_LENGTH)
        ]
    )
    last_name = serializers.CharField(
        required=True,
        validators=[MaxLengthValidator(
            MAX_USER,
            message=ERROR_MESSAGE_CHECK_LENGTH)
        ]
    )

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для Пользователей."""
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        validators=[
            MaxLengthValidator(
                MAX_USER,
                message=ERROR_MESSAGE_CHECK_LENGTH
            ),
            UniqueValidator(
                queryset=CustomUser.objects.all(),
                message=ERROR_MESSAGE_DOUBLE_USERNAME
            )
        ],
        required=True,
        error_messages={
            'invalid': ERROR_MESSAGE_REGEX
        }
    )
    email = serializers.EmailField(
        required=True,
        validators=[
            EmailValidator,
            UniqueValidator(
                queryset=CustomUser.objects.all(),
                message=ERROR_MESSAGE_DOUBLE_EMAIL
            )
        ]
    )
    password = serializers.CharField(write_only=True, required=True)
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        """Определяем значение поля is_subscribed для отображения."""
        user = self.context['request'].user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, following=obj).exists()
        return False

    def create(self, validated_data):
        """Создаем нового пользователя."""
        email = validated_data.pop('email')
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        user = CustomUser(email=email, username=username)
        user.set_password(password)
        user.save()
        return user


class MeSerializer(serializers.ModelSerializer):
    """Сериализатор Me."""
    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара."""
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = CustomUser
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для Тегов в рецепте."""

    class Meta:
        model = Tag
        fields = ('id',)


class TagListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка Тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для Ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id',)


class IngredientListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка Ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeIngredient."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeTagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeTag."""
    class Meta:
        model = RecipeTag
        fields = '__all__'


class RecipeMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""
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
        if 'tags' not in data or not data['tags']:
            raise serializers.ValidationError('Укажите хотя бы один тэг.')
        if 'ingredients' not in data or not data['ingredients']:
            raise serializers.ValidationError('Укажите ингредиенты.')
        if 'image' not in data or not data['image']:
            raise serializers.ValidationError('Добавьте изображенние рецепта.')
        ingredient_ids = set()
        tag_ids = set()
        for ingredients in data['ingredients']:
            ingredient_id = ingredients['id']
            amount = ingredients['amount']
            try:
                Ingredient.objects.get(pk=ingredient_id)
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    f'Ингредиент c ID {ingredient_id} не существует.'
                )
            if amount < 1:
                raise serializers.ValidationError(
                    'Необходимо указать количество ингредиента'
                )
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    f'Ингредиент c ID {ingredient_id} уже указан.'
                )
            ingredient_ids.add(ingredient_id)
        for tags in data['tags']:
            tag_id = tags.id
            try:
                Tag.objects.get(pk=tag_id)
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    f'Ингредиент c ID {tag_id} не существует.'
                )
            if tag_id in tag_ids:
                raise serializers.ValidationError(
                    f'Ингредиент c ID {tag_id} уже указан.'
                )
            tag_ids.add(tag_id)
        return data

    def create_recipe_ingredient(self, ingredients, recipe):
        """Создание записи в таблице RecipeIngredient."""
        for data in ingredients:
            pk = data['id']
            ingredient = Ingredient.objects.get(pk=pk)
            amount = data['amount']
            RecipeIngredient.objects.create(
                ingredient=ingredient, recipe=recipe, amount=amount
            )

    def create_recipe_tag(self, tags, recipe):
        """Создание записи в таблице RecipeTag."""
        recipe.tags.set(tags)

    def create(self, validated_data):
        """Создание рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_recipe_ingredient(ingredients, recipe)
        self.create_recipe_tag(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.name = validated_data['name']
        instance.text = validated_data['text']
        instance.cooking_time = validated_data['cooking_time']
        instance.image = validated_data.get('image')
        # if validated_data.get('image'):
        #     instance.image = validated_data['image']
        instance.ingredients.through.objects.filter(recipe=instance).delete()
        instance.tags.clear()
        self.create_recipe_ingredient(ingredients, instance)
        self.create_recipe_tag(tags, instance)
        instance.save()
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
    tags = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    author = CustomUserSerializer()
    image = serializers.ImageField(
        use_url=True,
        required=False,
        allow_null=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_tags(self, obj):
        recipe_tags = RecipeTag.objects.filter(recipe=obj)
        return [
            {
                'id': rt.tag.id,
                'name': rt.tag.name,
                'slug': rt.tag.slug
            }
            for rt in recipe_tags
        ]

    def get_ingredients(self, obj):
        """Возвращает список ингредиентов с количеством для данного рецепта."""
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return [
            {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': ri.ingredient.measurement_unit,
                'amount': ri.amount
            }
            for ri in recipe_ingredients
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для Подписок."""
    # recipes = serializers.SerializerMethodField(read_only=True)
    # recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            # 'is_subscribed',
            # 'recipes',
            # 'recipes_count',
            'avatar'
        )
        read_only_fields = ('email', 'username')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following')
            )
        ]

    # def get_is_subscribed(self, obj):
    #     request = self.context.get('request')
    #     if request:
    #         return Follow.objects.filter(
    #             user=request.user,
    #             following=obj
    #         ).exists()
    #     else:
    #         return False

    # def get_recipes(self, obj):
    #     recipes = obj.recipes.all()
    #     serializer = RecipeMiniSerializer(recipes, many=True, read_only=True)
    #     return serializer.data

    # @staticmethod
    # def get_recipes_count(obj):
    #     """Метод для получения количества рецептов."""
    #     return obj.recipes.count()

    # def validate_following(self, value):
    #     if self.context['request'].user == value:
    #         raise serializers.ValidationError(
    #             'Нельзя подписываться на самого себя!'
    #         )
    #     return value
