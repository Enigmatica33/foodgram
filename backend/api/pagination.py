from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)


class CustomPagination(PageNumberPagination):
    """Пагинатор для вывода определённого количества элементов на странице."""
    page_size_query_param = 'limit'  # количество объектов на странице
    page_query_param = 'page'
    max_page_size = 100              # Макс. объектов на странице


class LimitPagination(LimitOffsetPagination):
    """Кастомный пагинатор для вывода элементов на странице."""
    limit_query_param = 'limit'
    default_limit = 6
    max_limit = 100
