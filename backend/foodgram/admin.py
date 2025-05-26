from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (CustomUser, Ingredient, Recipe, RecipeIngredient,
                     RecipeTag, Tag)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    # Количество пустых форм,
    # доступных для добавления новых ингредиентов
    # Можно добавить дополнительные настройки для отображения
    # полей в админ-панели, если это необходимо
    fields = ('ingredient', 'amount')
    autocomplete_fields = ('ingredient',)


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag
    extra = 1  # Количество пустых форм для добавления новых тегов
    autocomplete_fields = ('tag',)


class RecipeAdmin(admin.ModelAdmin):
    model = Recipe
    list_display = ['author', 'name']
    list_filter = ['tags']
    search_fields = ['author', 'name']
    actions = ['delete_selected']
    inlines = (RecipeIngredientInline, RecipeTagInline)


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


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.empty_value_display = 'Не задано'
# admin.site.register(RecipeTag)
# admin.site.register(RecipeIngredient)
