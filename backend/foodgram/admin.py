from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)

User = get_user_model()


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    fields = ['ingredient', 'amount']
    autocomplete_fields = ['ingredient']


class RecipeAdmin(admin.ModelAdmin):
    model = Recipe
    list_display = ['author', 'name', 'favorites_count']
    list_filter = ['tags']
    search_fields = ['author__username', 'name']
    actions = ['delete_selected']
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(favorites_count=Count('recipe_favorite'))
        return queryset

    @admin.display(
        description='Количество добавлений в избранное'
    )
    def favorites_count(self, obj):
        return obj.favorites_count


class UserAdmin(BaseUserAdmin):
    model = User
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('email', 'username', 'first_name', 'last_name')}),
    )
    search_fields = ['email', 'username']


class TagAdmin(admin.ModelAdmin):
    model = Tag
    search_fields = ['name']
    actions = ['delete_selected']


class IngredientAdmin(admin.ModelAdmin):
    model = Ingredient
    list_display = ['name', 'measurement_unit']
    search_fields = ['name']
    actions = ['delete_selected']


class FavoriteAdmin(admin.ModelAdmin):
    model = Favorite
    list_display = ['user', 'recipe']


class FollowAdmin(admin.ModelAdmin):
    model = Follow
    list_display = ['user', 'following']


class ShoppingCartAdmin(admin.ModelAdmin):
    model = ShoppingCart
    list_display = ['user', 'recipe']


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.empty_value_display = 'Не задано'
