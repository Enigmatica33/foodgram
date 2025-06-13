from django.db import models
from django.db.models import Exists, OuterRef, Value


class RecipeQuerySet(models.QuerySet):
    def with_user_annotations(self, user, FavoriteModel,
                              ShoppingCartModel, RecipeModel):
        """
        Аннотирует queryset рецептов флагами is_favorite
        и is_in_shopping_cart для указанного пользователя.
        """
        queryset = RecipeModel.objects.select_related(
            'author').prefetch_related(
            'tags',
            'recipeingredient__ingredient'
        )
        if user.is_authenticated:
            queryset = queryset.annotate(is_favorited=Exists(
                FavoriteModel.objects.filter(
                    user=user,
                    recipe=OuterRef('pk')
                )),
                is_in_shopping_cart=Exists(
                    ShoppingCartModel.objects.filter(
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
