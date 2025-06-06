from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Пагинатор для вывода определённого количества элементов на странице."""
    page_size_query_param = 'limit'  # количество объектов на странице
    page_query_param = 'page'        # номер страницы
    max_page_size = 100              # Макс. объектов на странице
