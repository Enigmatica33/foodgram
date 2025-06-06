from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Пагинатор для вывода определённого количества элементов на странице."""
    page_size_query_param = 'limit'  # Параметр для указания количества объектов на странице
    page_query_param = 'page'        # Параметр для указания номера страницы
    max_page_size = 100              # Максимальное количество объектов на странице
