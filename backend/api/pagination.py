from rest_framework.pagination import LimitOffsetPagination


class LimitPagination(LimitOffsetPagination):
    """Кастомный пагинатор для вывода элементов на странице."""
    limit_query_param = 'limit'
    default_limit = 6
    max_limit = 100
