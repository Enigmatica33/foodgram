from django.db import models
from django.db.models import Exists, OuterRef, Value

from foodgram.models import Favorite, Recipe, ShoppingCart


class RecipeQuerySet(models.Queryset):
    def with_user_annotations(self, user):
        """
        Аннотирует queryset рецептов флагами is_favorite
        и is_in_shopping_cart для указанного пользователя.
        """
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
