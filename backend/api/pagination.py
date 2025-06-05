from rest_framework.pagination import LimitOffsetPagination


class LimitPagination(LimitOffsetPagination):
    """Пагинатор для вывода определенного количества элементов на странице."""
    limit_query_param = 'limit'
    default_limit = 6
    max_limit = 100
