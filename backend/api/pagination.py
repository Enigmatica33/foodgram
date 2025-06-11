from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class Pagination(PageNumberPagination):
    """Пагинатор для вывода определённого количества элементов на странице."""
    page_size_query_param = 'limit'
    page_query_param = 'page'
    max_page_size = settings.MAX_PAGE_SIZE
    page_size = settings.PAGE_SIZE
