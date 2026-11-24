
from rest_framework.pagination import PageNumberPagination


class AccessRecordPagination(PageNumberPagination):
    """
    Paginación exclusiva del historial de accesos.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"
