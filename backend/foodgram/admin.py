from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (CustomUser, Favorite, Follow, Ingredient, Recipe,
                     RecipeIngredient, RecipeTag, ShoppingCart, Tag)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    fields = ['ingredient', 'amount']
    autocomplete_fields = ['ingredient']


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag
    extra = 1
    autocomplete_fields = ['tag']


class RecipeAdmin(admin.ModelAdmin):
    model = Recipe
    list_display = ['author', 'name', 'favorites_count']
    list_filter = ['tags']
    search_fields = ['author__username', 'name']
    actions = ['delete_selected']
    inlines = (RecipeIngredientInline, RecipeTagInline)

    def favorites_count(self, obj):
        return obj.recipe_favorite.count()
    favorites_count.short_description = 'Количество добавлений в избранное'


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_fieldsets = UserAdmin.add_fieldsets + (
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
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.empty_value_display = 'Не задано'
# admin.site.register(RecipeTag)
# admin.site.register(RecipeIngredient)
