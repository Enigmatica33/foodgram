from django.urls import path

from .views import redirect_from_short_link

app_name = 'foodgram'

urlpatterns = [
    path(
        's/<str:recipe_hash>/',
        redirect_from_short_link,
        name='short_link_redirect'
    )
]
